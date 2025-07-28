#!/usr/bin/env python3
"""
Enhanced RethinkDB to MySQL Migration Script
Uses .info files for proper schema reconstruction and data migration
"""
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
import pymysql
from tqdm import tqdm


class RethinkDBMigrator:
    def __init__(self, dump_path: str, config: Dict[str, Any]):
        self.dump_path = dump_path
        self.config = config
        self.connection = None
        self.stats = {"success": 0, "failed": 0, "total_records": 0}
        self.dry_run = config.get("dry_run", False)

    def connect_to_mysql(self) -> Optional[pymysql.Connection]:
        """Establish MySQL connection"""
        if self.dry_run:
            print("✓ DRY RUN: Skipping MySQL connection")
            return None

        try:
            mysql_config = self.config["mysql"]
            self.connection = pymysql.connect(
                **mysql_config, cursorclass=pymysql.cursors.DictCursor, autocommit=True
            )
            print(f"✓ Connected to MySQL database: {mysql_config['database']}")
            return self.connection
        except Exception as e:
            print(f"✗ Failed to connect to MySQL: {e}")
            sys.exit(1)

    def parse_info_file(self, info_file: str) -> Dict[str, Any]:
        """Parse .info file to extract table metadata"""
        try:
            with open(info_file, "r") as f:
                info_data = json.load(f)
            return info_data
        except Exception as e:
            print(f"Warning: Could not parse {info_file}: {e}")
            return {}

    def analyze_data_types(self, data: List[Dict]) -> Dict[str, Dict]:
        """Analyze actual data to determine optimal MySQL column types"""
        if not data:
            return {}

        schema = {}
        sample_size = min(1000, len(data))

        print(f"  Analyzing data types from {sample_size} sample records...")

        # First pass: analyze types from sample
        for record in tqdm(data[:sample_size], desc="  Analyzing sample", leave=False):
            for field_name, value in record.items():
                if field_name not in schema:
                    schema[field_name] = {
                        "type": "TEXT",
                        "max_length": 0,
                        "nullable": True,
                        "is_primary": field_name == "id",
                        "is_foreign_key": field_name.endswith("_id")
                        and field_name != "id",
                        "is_timestamp": False,
                        "is_json": False,
                        "sample_values": [],
                    }

                # Track sample values for analysis
                if len(schema[field_name]["sample_values"]) < 5:
                    schema[field_name]["sample_values"].append(value)

                # Check for null values
                if value is None:
                    schema[field_name]["nullable"] = True
                    continue

                # Determine data type
                if isinstance(value, bool):
                    schema[field_name]["type"] = "BOOLEAN"
                elif isinstance(value, int):
                    if abs(value) > 2147483647:
                        schema[field_name]["type"] = "BIGINT"
                    else:
                        schema[field_name]["type"] = "INT"
                elif isinstance(value, float):
                    schema[field_name]["type"] = "DECIMAL(15,4)"
                elif isinstance(value, str):
                    schema[field_name]["max_length"] = max(
                        schema[field_name]["max_length"], len(value)
                    )

                    # Detect timestamp patterns
                    if self._is_timestamp_field(field_name, value):
                        schema[field_name]["type"] = "DATETIME"
                        schema[field_name]["is_timestamp"] = True
                    elif field_name.lower() in ["email"]:
                        schema[field_name]["type"] = "VARCHAR(255)"
                    elif field_name.lower() in ["phone", "mobile"]:
                        schema[field_name]["type"] = "VARCHAR(20)"
                    elif (
                        schema[field_name]["is_primary"]
                        or schema[field_name]["is_foreign_key"]
                    ):
                        schema[field_name]["type"] = "VARCHAR(255)"
                    else:
                        # Determine VARCHAR vs TEXT based on length
                        max_len = schema[field_name]["max_length"]
                        if max_len <= 100:
                            schema[field_name][
                                "type"
                            ] = f"VARCHAR({max(max_len * 4, 255)})"
                        elif max_len <= 500:
                            schema[field_name][
                                "type"
                            ] = f"VARCHAR({max(max_len * 3, 1000)})"
                        elif max_len <= 2000:
                            schema[field_name]["type"] = f"VARCHAR({max_len * 2})"
                        else:
                            schema[field_name]["type"] = "TEXT"

                elif isinstance(value, dict):
                    # Handle RethinkDB TIME objects
                    if value.get("$reql_type$") == "TIME":
                        schema[field_name]["type"] = "DATETIME"
                        schema[field_name]["is_timestamp"] = True
                    else:
                        schema[field_name]["type"] = "JSON"
                        schema[field_name]["is_json"] = True
                elif isinstance(value, list):
                    schema[field_name]["type"] = "JSON"
                    schema[field_name]["is_json"] = True

        # Second pass: scan all data for maximum string lengths
        print(f"  Scanning {len(data)} records for maximum field lengths...")
        for record in tqdm(data, desc="  Scanning lengths", leave=False):
            for field_name, value in record.items():
                if field_name in schema and isinstance(value, str):
                    schema[field_name]["max_length"] = max(
                        schema[field_name]["max_length"], len(value)
                    )

        # Update VARCHAR sizes based on actual maximum lengths found
        for field_name, field_info in schema.items():
            if (
                "VARCHAR" in field_info["type"]
                and not field_info["is_primary"]
                and not field_info["is_foreign_key"]
            ):
                max_len = field_info["max_length"]
                if max_len > 0:
                    if max_len <= 100:
                        field_info["type"] = f"VARCHAR({max(max_len * 4, 255)})"
                    elif max_len <= 500:
                        field_info["type"] = f"VARCHAR({max(max_len * 3, 2000)})"
                    elif max_len <= 2000:
                        field_info["type"] = f"VARCHAR({max_len * 2})"
                    else:
                        field_info["type"] = "TEXT"

        return schema

    def _is_timestamp_field(self, field_name: str, value: str) -> bool:
        """Check if field appears to be a timestamp"""
        timestamp_patterns = ["time", "date", "created", "updated", "at"]
        field_lower = field_name.lower()

        if isinstance(value, str):
            # ISO 8601 format
            if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
                return True
            # MySQL datetime format
            if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value):
                return True
            # Custom format like '03/03/2025, 13:01:14'
            if re.match(r"\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}", value):
                return True
            else:
                return False

        if any(pattern in field_lower for pattern in timestamp_patterns):
            return True

        return False

    def generate_create_table_sql(
        self, table_name: str, schema: Dict, info_data: Dict
    ) -> str:
        """Generate CREATE TABLE SQL using schema analysis and .info metadata"""
        columns = []
        indexes = []
        primary_key = info_data.get("primary_key", "id")

        # Process each column
        for field_name, field_info in schema.items():
            column_type = field_info["type"]
            nullable = (
                "NULL"
                if field_info["nullable"] and field_name != primary_key
                else "NOT NULL"
            )

            # Primary key handling
            if field_name == primary_key:
                if "VARCHAR" in column_type:
                    columns.append(f"`{field_name}` {column_type} NOT NULL")
                else:
                    columns.append(f"`{field_name}` VARCHAR(255) NOT NULL")
            else:
                columns.append(f"`{field_name}` {column_type} {nullable}")

            # Add indexes for foreign keys
            if field_info["is_foreign_key"]:
                if "TEXT" in column_type or "BLOB" in column_type:
                    indexes.append(f"INDEX `idx_{field_name}` (`{field_name}`(191))")
                else:
                    indexes.append(f"INDEX `idx_{field_name}` (`{field_name}`)")

        # Process indexes from .info file
        for index_info in info_data.get("indexes", []):
            index_name = index_info.get("index")
            if index_name and index_name != primary_key:
                if index_name in schema:
                    column_type = schema[index_name]["type"]
                    if "TEXT" in column_type or "BLOB" in column_type:
                        index_sql = f"INDEX `idx_{index_name}` (`{index_name}`(191))"
                    else:
                        index_sql = f"INDEX `idx_{index_name}` (`{index_name}`)"

                    if index_sql not in indexes:
                        indexes.append(index_sql)
                else:
                    print(
                        f"Warning: Index on '{index_name}' skipped - column not found in data"
                    )

        # Build final SQL
        sql_parts = [f"CREATE TABLE `{table_name}` ("]
        sql_parts.append("  " + ",\n  ".join(columns))
        sql_parts.append(f",\n  PRIMARY KEY (`{primary_key}`)")

        if indexes:
            sql_parts.append(",\n  " + ",\n  ".join(indexes))

        sql_parts.append(
            "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        )

        return "\n".join(sql_parts)

    def convert_value_for_mysql(self, value: Any) -> Any:
        """Convert RethinkDB values to MySQL-compatible format"""
        if value is None:
            return None
        elif isinstance(value, dict):
            # Handle RethinkDB TIME objects
            if value.get("$reql_type$") == "TIME":
                try:
                    epoch_time = value.get("epoch_time")
                    if epoch_time:
                        dt = datetime.fromtimestamp(epoch_time)
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
                return None
            else:
                return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        else:
            return value

    def _convert_datetime_string(self, value: str) -> str:
        """Convert various datetime string formats to MySQL datetime format"""
        if not isinstance(value, str):
            return value

        # ISO datetime strings
        if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        # Handle format like '03/03/2025, 13:01:14'
        elif re.match(r"\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}", value):
            try:
                dt = datetime.strptime(value, "%d/%m/%Y, %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        # Handle MySQL datetime format
        elif re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value):
            return value

        return value

    def migrate_table(self, table_name: str) -> bool:
        """Migrate a single table using .info and .json files"""
        try:
            print(
                f"\n=== {'[DRY RUN] ' if self.dry_run else ''}Migrating {table_name} ==="
            )

            json_file = os.path.join(self.dump_path, f"{table_name}.json")
            info_file = os.path.join(self.dump_path, f"{table_name}.info")

            if not os.path.exists(json_file):
                print(f"Warning: {json_file} not found, skipping...")
                return True

            # Load data
            with open(json_file, "r") as f:
                data = json.load(f)

            if not data:
                print(f"No data found in {table_name}, creating empty table...")
                data = []
            else:
                print(f"Found {len(data)} records")

            # Parse .info file
            info_data = {}
            if os.path.exists(info_file):
                info_data = self.parse_info_file(info_file)
                print(f"✓ Parsed schema metadata from {table_name}.info")
            else:
                print(f"Warning: {info_file} not found, using data analysis only")

            # Analyze data types
            if data:
                schema = self.analyze_data_types(data)
            else:
                primary_key = info_data.get("primary_key", "id")
                schema = {
                    primary_key: {
                        "type": "VARCHAR(255)",
                        "nullable": False,
                        "is_primary": True,
                        "is_foreign_key": False,
                        "is_timestamp": False,
                        "is_json": False,
                    }
                }

            # Generate CREATE TABLE SQL
            create_sql = self.generate_create_table_sql(table_name, schema, info_data)

            if self.dry_run:
                print(f"✓ [DRY RUN] Would create table with SQL:")
                print(create_sql)
                print(f"✓ [DRY RUN] Would insert {len(data)} records")
            else:
                cursor = self.connection.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                cursor.execute(create_sql)
                print(f"✓ Created table structure")

                # Insert data if any exists
                if data:
                    self._insert_data(cursor, table_name, schema, data)

            print(
                f"✓ Successfully {'analyzed' if self.dry_run else 'migrated'} {table_name}"
            )
            self.stats["success"] += 1
            self.stats["total_records"] += len(data)
            return True

        except Exception as e:
            print(
                f"✗ Error {'analyzing' if self.dry_run else 'migrating'} {table_name}: {e}"
            )
            self.stats["failed"] += 1
            return False

    def _insert_data(self, cursor, table_name: str, schema: Dict, data: List[Dict]):
        """Insert data into MySQL table"""
        columns = list(schema.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in columns])}) VALUES ({placeholders})"

        batch_size = self.config.get("migration", {}).get("batch_size", 1000)
        total_records = len(data)

        with tqdm(total=total_records, desc=f"  Inserting {table_name}") as pbar:
            for i in range(0, total_records, batch_size):
                batch = data[i : i + batch_size]
                batch_data = []

                for record in batch:
                    row_data = []
                    for col in columns:
                        value = record.get(col)
                        converted_value = self.convert_value_for_mysql(value)

                        # Handle datetime conversion for timestamp fields
                        if schema[col]["is_timestamp"] and isinstance(
                            converted_value, str
                        ):
                            converted_value = self._convert_datetime_string(
                                converted_value
                            )

                        row_data.append(converted_value)
                    batch_data.append(row_data)

                cursor.executemany(insert_sql, batch_data)
                pbar.update(len(batch))

    def migrate_all_tables(self):
        """Migrate all tables in the dump directory"""
        print(
            f"=== {'[DRY RUN] ' if self.dry_run else ''}Enhanced RethinkDB to MySQL Migration ==="
        )

        # Find all available tables
        json_files = [f for f in os.listdir(self.dump_path) if f.endswith(".json")]
        available_tables = [f.replace(".json", "") for f in json_files]

        print(
            f"Found {len(available_tables)} tables to {'analyze' if self.dry_run else 'migrate'}"
        )

        # Get table processing order
        table_order = self.config.get("migration", {}).get("table_order", [])
        processed_tables = set()

        # First, process tables in defined order
        for table_name in table_order:
            if table_name in available_tables:
                self.migrate_table(table_name)
                processed_tables.add(table_name)

        # Then process any remaining tables
        for table_name in available_tables:
            if table_name not in processed_tables:
                self.migrate_table(table_name)

        self._print_migration_summary()

    def _print_migration_summary(self):
        """Print final migration statistics"""
        action = "Analysis" if self.dry_run else "Migration"
        print(f"\n=== {action} Summary ===")
        print(
            f"✓ Successfully {'analyzed' if self.dry_run else 'migrated'}: {self.stats['success']} tables"
        )
        print(
            f"✗ Failed {'analyses' if self.dry_run else 'migrations'}: {self.stats['failed']} tables"
        )
        print(
            f"Total records {'analyzed' if self.dry_run else 'migrated'}: {self.stats['total_records']:,}"
        )

        if not self.dry_run and self.connection:
            # Show table statistics
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT table_name, table_rows 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                ORDER BY table_name
            """,
                (self.config["mysql"]["database"],),
            )

            print(f"\n=== Database Statistics ===")
            for row in cursor.fetchall():
                table_rows = row["TABLE_ROWS"] or 0
                print(f"{row['TABLE_NAME']}: {table_rows:,} rows")

        if self.stats["failed"] == 0:
            print(f"\n🎉 {action} completed successfully!")
        else:
            print(f"\n⚠️  {action} completed with {self.stats['failed']} errors")
