# Migration Example

This example shows how to migrate a RethinkDB database to MySQL using the migration tool.

## Step 1: Create RethinkDB Dump

```bash
# Connect to your RethinkDB instance and create a dump
rethinkdb dump -c localhost:28015 -f dbname_dump.tar.gz

# Or if RethinkDB is on a different host/port
rethinkdb dump -c production-server:28015 -f dbname_dump.tar.gz
```

## Step 2: Extract the Dump

```bash
# Extract the tar.gz file
tar -xzf dbname_dump.tar.gz

# This creates a directory structure like:
# rethinkdb_dump_2024_07_24_19_30_00/
# └── dbname/
#     ├── Users.info
#     ├── Users.json
#     ├── Products.info
#     ├── Products.json
#     └── ...
```

## Step 3: Prepare MySQL Database

```sql
-- Create the target database
CREATE DATABASE dbname CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a user for the migration (optional but recommended)
CREATE USER 'migration_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON dbname.* TO 'migration_user'@'localhost';
FLUSH PRIVILEGES;
```

## Step 4: Run Migration

### Basic Migration

```bash
# Set environment variables
export MYSQL_PASSWORD=secure_password
export MYSQL_DATABASE=dbname

# Run the migration
python -m mysql_migrator rethinkdb_dump_2024_07_24_19_30_00/dbname/
```

### Migration with Configuration File

```bash
# Create config.json (see examples/config.json)
python -m mysql_migrator rethinkdb_dump_2024_07_24_19_30_00/dbname/ --config config.json
```

### Dry Run First (Recommended)

```bash
# Test the migration without actually executing it
python -m mysql_migrator rethinkdb_dump_2024_07_24_19_30_00/dbname/ --dry-run
```

## Step 5: Verify Migration

```sql
-- Check tables were created
SHOW TABLES;

-- Check record counts
SELECT 
    table_name, 
    table_rows 
FROM information_schema.tables 
WHERE table_schema = 'dbname';

-- Verify data integrity (example)
SELECT COUNT(*) FROM Users;
SELECT * FROM Users LIMIT 5;
```

## Example Output

```
=== Enhanced RethinkDB to MySQL Migration ===
Found 15 tables to migrate

=== Migrating Users ===
Found 1250 records
  Analyzing data types from 1000 sample records...
  Scanning 1250 records for maximum field lengths...
✓ Parsed schema metadata from Users.info
✓ Created table structure
  Inserting Users: 100%|████████████| 1250/1250 [00:02<00:00, 625.00it/s]
✓ Successfully migrated Users

=== Migration Summary ===
✓ Successfully migrated: 15 tables
✗ Failed migrations: 0 tables
Total records migrated: 45,230

🎉 Migration completed successfully!
```

## Troubleshooting

### Large Datasets

For very large datasets, you might need to:

```bash
# Increase batch size for better performance
python -m mysql_migrator dump/ --batch-size 5000

# Or decrease if you're running into memory issues
python -m mysql_migrator dump/ --batch-size 500
```

### MySQL Configuration

Add these to your MySQL configuration for better performance:

```ini
[mysqld]
max_allowed_packet = 1G
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
```

### Custom Table Order

If you have foreign key dependencies, create a table order file:

```json
[
  "Users",
  "Categories", 
  "Products",
  "Orders",
  "OrderItems"
]
```

Then use it:

```bash
python -m mysql_migrator dump/ --table-order table_order.json
```
