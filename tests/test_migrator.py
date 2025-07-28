#!/usr/bin/env python3
"""
Basic tests for RethinkDB to MySQL Migrator
"""
import unittest
import json
import tempfile
import os
from datetime import datetime

from mysql_migrator.migrator import RethinkDBMigrator


class TestRethinkDBMigrator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "user": "test",
                "password": "test",
                "database": "test_db",
                "charset": "utf8mb4"
            },
            "migration": {
                "batch_size": 100,
                "table_order": []
            },
            "dry_run": True  # Always use dry run for tests
        }
        
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_data_type_analysis(self):
        """Test data type analysis functionality"""
        migrator = RethinkDBMigrator(self.temp_dir, self.config)
        
        # Sample data with various types
        test_data = [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "height": 5.9,
                "is_active": True,
                "created_at": {"$reql_type$": "TIME", "epoch_time": 1640995200.0, "timezone": "+00:00"},
                "metadata": {"role": "admin", "permissions": ["read", "write"]},
                "tags": ["user", "premium"]
            },
            {
                "id": "456e7890-e89b-12d3-a456-426614174001", 
                "name": "Jane Smith",
                "email": "jane@example.com",
                "age": 25,
                "height": 5.5,
                "is_active": False,
                "created_at": {"$reql_type$": "TIME", "epoch_time": 1640995300.0, "timezone": "+00:00"},
                "metadata": {"role": "user", "permissions": ["read"]},
                "tags": ["user"]
            }
        ]
        
        schema = migrator.analyze_data_types(test_data)
        
        # Test expected data types
        self.assertEqual(schema["id"]["type"], "VARCHAR(255)")
        self.assertTrue(schema["id"]["is_primary"])
        
        self.assertIn("VARCHAR", schema["name"]["type"])
        self.assertIn("VARCHAR", schema["email"]["type"])
        
        self.assertEqual(schema["age"]["type"], "INT")
        self.assertEqual(schema["height"]["type"], "DECIMAL(15,4)")
        self.assertEqual(schema["is_active"]["type"], "BOOLEAN")
        
        self.assertEqual(schema["created_at"]["type"], "DATETIME")
        self.assertTrue(schema["created_at"]["is_timestamp"])
        
        self.assertEqual(schema["metadata"]["type"], "JSON")
        self.assertTrue(schema["metadata"]["is_json"])
        
        self.assertEqual(schema["tags"]["type"], "JSON")
        self.assertTrue(schema["tags"]["is_json"])
    
    def test_value_conversion(self):
        """Test RethinkDB value conversion to MySQL format"""
        migrator = RethinkDBMigrator(self.temp_dir, self.config)
        
        # Test TIME object conversion
        time_obj = {"$reql_type$": "TIME", "epoch_time": 1640995200.0, "timezone": "+00:00"}
        converted = migrator.convert_value_for_mysql(time_obj)
        self.assertEqual(converted, "2022-01-01 00:00:00")
        
        # Test JSON object conversion
        json_obj = {"key": "value", "nested": {"data": 123}}
        converted = migrator.convert_value_for_mysql(json_obj)
        self.assertEqual(converted, '{"key": "value", "nested": {"data": 123}}')
        
        # Test array conversion
        array_obj = ["item1", "item2", 123]
        converted = migrator.convert_value_for_mysql(array_obj)
        self.assertEqual(converted, '["item1", "item2", 123]')
        
        # Test null value
        self.assertIsNone(migrator.convert_value_for_mysql(None))
        
        # Test regular values
        self.assertEqual(migrator.convert_value_for_mysql("string"), "string")
        self.assertEqual(migrator.convert_value_for_mysql(123), 123)
        self.assertEqual(migrator.convert_value_for_mysql(True), True)
    
    def test_timestamp_detection(self):
        """Test timestamp field detection"""
        migrator = RethinkDBMigrator(self.temp_dir, self.config)
        
        # Test various timestamp formats
        self.assertTrue(migrator._is_timestamp_field("created_at", "2022-01-01T00:00:00"))
        self.assertTrue(migrator._is_timestamp_field("updated_at", "2022-01-01 00:00:00"))
        self.assertTrue(migrator._is_timestamp_field("timestamp", "01/01/2022, 00:00:00"))
        
        # Test non-timestamp values
        self.assertFalse(migrator._is_timestamp_field("name", "John Doe"))
        self.assertFalse(migrator._is_timestamp_field("created_at", "not-a-date"))
    
    def test_create_table_sql_generation(self):
        """Test CREATE TABLE SQL generation"""
        migrator = RethinkDBMigrator(self.temp_dir, self.config)
        
        schema = {
            "id": {
                "type": "VARCHAR(255)",
                "nullable": False,
                "is_primary": True,
                "is_foreign_key": False,
                "is_timestamp": False,
                "is_json": False
            },
            "name": {
                "type": "VARCHAR(255)",
                "nullable": False,
                "is_primary": False,
                "is_foreign_key": False,
                "is_timestamp": False,
                "is_json": False
            },
            "user_id": {
                "type": "VARCHAR(255)",
                "nullable": True,
                "is_primary": False,
                "is_foreign_key": True,
                "is_timestamp": False,
                "is_json": False
            }
        }
        
        info_data = {
            "primary_key": "id",
            "indexes": [
                {"index": "name"},
                {"index": "user_id"}
            ]
        }
        
        sql = migrator.generate_create_table_sql("test_table", schema, info_data)
        
        # Check that SQL contains expected elements
        self.assertIn("CREATE TABLE `test_table`", sql)
        self.assertIn("PRIMARY KEY (`id`)", sql)
        self.assertIn("`name` VARCHAR(255) NOT NULL", sql)
        self.assertIn("`user_id` VARCHAR(255) NULL", sql)
        self.assertIn("INDEX `idx_user_id`", sql)
        self.assertIn("ENGINE=InnoDB", sql)
        self.assertIn("utf8mb4", sql)


if __name__ == "__main__":
    unittest.main()
