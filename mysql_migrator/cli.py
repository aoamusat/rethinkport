#!/usr/bin/env python3
"""
Command Line Interface for RethinkDB to MySQL Migration Tool
"""
import argparse
import json
import os
import sys
from typing import Dict, Any

from .migrator import RethinkDBMigrator


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_path}: {e}")
        sys.exit(1)


def build_config(args) -> Dict[str, Any]:
    """Build configuration from command line arguments and config file"""
    config = {
        "mysql": {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "migrated_db",
            "charset": "utf8mb4",
        },
        "migration": {"batch_size": 1000, "table_order": []},
        "dry_run": False,
    }

    # Load config file if provided
    if args.config:
        file_config = load_config_file(args.config)
        # Merge file config with defaults
        if "mysql" in file_config:
            config["mysql"].update(file_config["mysql"])
        if "migration" in file_config:
            config["migration"].update(file_config["migration"])

    # Override with command line arguments
    if args.host:
        config["mysql"]["host"] = args.host
    if args.port:
        config["mysql"]["port"] = args.port
    if args.user:
        config["mysql"]["user"] = args.user
    if args.password:
        config["mysql"]["password"] = args.password
    if args.database:
        config["mysql"]["database"] = args.database
    if args.batch_size:
        config["migration"]["batch_size"] = args.batch_size
    if args.table_order:
        with open(args.table_order, "r") as f:
            config["migration"]["table_order"] = json.load(f)

    config["dry_run"] = args.dry_run

    # Get password from environment if not provided
    if not config["mysql"]["password"]:
        config["mysql"]["password"] = os.environ.get("MYSQL_PASSWORD", "")

    # Get other MySQL settings from environment
    config["mysql"]["host"] = os.environ.get("MYSQL_HOST", config["mysql"]["host"])
    config["mysql"]["port"] = int(os.environ.get("MYSQL_PORT", config["mysql"]["port"]))
    config["mysql"]["user"] = os.environ.get("MYSQL_USER", config["mysql"]["user"])
    config["mysql"]["database"] = os.environ.get(
        "MYSQL_DATABASE", config["mysql"]["database"]
    )

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration"""
    mysql_config = config["mysql"]

    if not mysql_config["database"]:
        print("Error: MySQL database name is required")
        return False

    if not config.get("dry_run", False) and not mysql_config["password"]:
        print(
            "Warning: No MySQL password provided. Set MYSQL_PASSWORD environment variable or use --password"
        )

    return True


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="RethinkPort 🚢 - Port your RethinkDB data to MySQL with confidence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic migration
  python -m mysql_migrator /path/to/dump/
  # Or after installation: rethinkport /path/to/dump/

  # With custom MySQL settings
  rethinkport /path/to/dump/ \\
    --host localhost --port 3306 --user root --database myapp

  # Using configuration file
  rethinkport /path/to/dump/ --config config.json

  # Dry run to see what would be migrated
  rethinkport /path/to/dump/ --dry-run

Environment Variables:
  MYSQL_HOST        MySQL host (default: localhost)
  MYSQL_PORT        MySQL port (default: 3306)
  MYSQL_USER        MySQL username (default: root)
  MYSQL_PASSWORD    MySQL password
  MYSQL_DATABASE    MySQL database name
        """,
    )

    parser.add_argument("dump_path", help="Path to extracted RethinkDB dump directory")

    parser.add_argument("--config", help="Configuration file path (JSON format)")

    # MySQL connection options
    mysql_group = parser.add_argument_group("MySQL Connection")
    mysql_group.add_argument("--host", help="MySQL host (default: localhost)")
    mysql_group.add_argument("--port", type=int, help="MySQL port (default: 3306)")
    mysql_group.add_argument("--user", help="MySQL username (default: root)")
    mysql_group.add_argument(
        "--password", help="MySQL password (or set MYSQL_PASSWORD env var)"
    )
    mysql_group.add_argument("--database", help="MySQL database name (required)")

    # Migration options
    migration_group = parser.add_argument_group("Migration Options")
    migration_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without executing",
    )
    migration_group.add_argument(
        "--batch-size", type=int, help="Batch size for data insertion (default: 1000)"
    )
    migration_group.add_argument(
        "--table-order",
        help="Custom table processing order (JSON file with array of table names)",
    )

    args = parser.parse_args()

    # Validate dump path
    if not os.path.exists(args.dump_path):
        print(f"Error: Dump path {args.dump_path} does not exist")
        sys.exit(1)

    if not os.path.isdir(args.dump_path):
        print(f"Error: {args.dump_path} is not a directory")
        sys.exit(1)

    # Build configuration
    config = build_config(args)

    # Validate configuration
    if not validate_config(config):
        sys.exit(1)

    # Show configuration in dry run mode
    if config["dry_run"]:
        print("=== Configuration ===")
        print(f"Dump path: {args.dump_path}")
        print(f"MySQL host: {config['mysql']['host']}:{config['mysql']['port']}")
        print(f"MySQL user: {config['mysql']['user']}")
        print(f"MySQL database: {config['mysql']['database']}")
        print(f"Batch size: {config['migration']['batch_size']}")
        if config["migration"]["table_order"]:
            print(f"Table order: {', '.join(config['migration']['table_order'])}")
        print()

    # Run migration
    migrator = RethinkDBMigrator(args.dump_path, config)
    migrator.connect_to_mysql()
    migrator.migrate_all_tables()


if __name__ == "__main__":
    main()
