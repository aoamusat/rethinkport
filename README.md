# RethinkPort 🚢

A comprehensive tool for migrating RethinkDB databases to MySQL, designed to work with official RethinkDB dump files.

**Port your RethinkDB data to MySQL with confidence.**

## Overview

This tool was created to address the lack of reliable migration tools for moving from RethinkDB to MySQL. It handles the complete migration pipeline including:

- Schema inference and optimization
- Data type conversion (including RethinkDB-specific types)
- Index and constraint migration
- Foreign key dependency management
- Batch processing for large datasets

## Features

- ✅ **Official RethinkDB dump support** - Works with `rethinkdb dump` output
- ✅ **Smart schema inference** - Analyzes data to create optimal MySQL schemas
- ✅ **Data type conversion** - Handles RethinkDB TIME objects, JSON, arrays
- ✅ **Index migration** - Preserves indexes and primary keys from .info files
- ✅ **Dependency management** - Processes tables in correct order for foreign keys
- ✅ **Batch processing** - Efficient handling of large datasets
- ✅ **Progress tracking** - Real-time migration statistics
- ✅ **Error handling** - Comprehensive logging and error reporting

## Installation

### Prerequisites

- Python 3.7+
- MySQL 5.7+ or MariaDB 10.2+
- RethinkDB (for creating dumps)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install from PyPI

```bash
pip install rethinkport
```

### Install from Source

```bash
git clone https://github.com/yourusername/rethinkport.git
cd rethinkport
pip install -e .
```

## Usage

### Step 1: Create RethinkDB Dump

First, create a dump of your RethinkDB database:

```bash
rethinkdb dump -c <host:port> -f my_database_dump.tar.gz
```

### Step 2: Extract the Dump

```bash
tar -xzf my_database_dump.tar.gz
```

This creates a directory structure like:
```
rethinkdb_dump_<date>/
└── <database_name>/
    ├── Table1.info
    ├── Table1.json
    ├── Table2.info
    ├── Table2.json
    └── ...
```

### Step 3: Run the Migration

#### Basic Usage

```bash
rethinkport /path/to/rethinkdb_dump_<date>/<database_name>/
```

#### With Configuration File

```bash
rethinkport /path/to/dump/ --config config.json
```

#### Command Line Options

```bash
rethinkport --help

usage: rethinkport [-h] [--config CONFIG] [--host HOST] [--port PORT]
                   [--user USER] [--password PASSWORD] [--database DATABASE]
                   [--dry-run] [--batch-size BATCH_SIZE] [--table-order TABLE_ORDER]
                   dump_path

RethinkPort 🚢 - Port your RethinkDB data to MySQL with confidence

positional arguments:
  dump_path             Path to extracted RethinkDB dump directory

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Configuration file path
  --host HOST           MySQL host (default: localhost)
  --port PORT           MySQL port (default: 3306)
  --user USER           MySQL username (default: root)
  --password PASSWORD   MySQL password
  --database DATABASE   MySQL database name
  --dry-run             Show what would be migrated without executing
  --batch-size BATCH_SIZE
                        Batch size for data insertion (default: 1000)
  --table-order TABLE_ORDER
                        Custom table processing order (JSON file)
```

## Configuration

### Environment Variables

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=your_database
```

### Configuration File

Create a `config.json` file:

```json
{
  "mysql": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "your_database",
    "charset": "utf8mb4"
  },
  "migration": {
    "batch_size": 1000,
    "table_order": [
      "Users",
      "Products",
      "Orders"
    ]
  }
}
```

## Data Type Mapping

| RethinkDB Type | MySQL Type | Notes |
|----------------|------------|-------|
| String (short) | VARCHAR(255) | Auto-sized based on data |
| String (long) | TEXT | For strings > 2000 chars |
| Number (int) | INT/BIGINT | Based on value range |
| Number (float) | DECIMAL(15,4) | Preserves precision |
| Boolean | BOOLEAN | Direct mapping |
| Object | JSON | RethinkDB objects → MySQL JSON |
| Array | JSON | RethinkDB arrays → MySQL JSON |
| TIME | DATETIME | Converts epoch_time to MySQL datetime |
| UUID | VARCHAR(255) | For primary/foreign keys |

## Examples

### Basic Migration

```bash
# Dump RethinkDB
rethinkdb dump -c localhost:28015 -f myapp_dump.tar.gz

# Extract
tar -xzf myapp_dump.tar.gz

# Migrate
rethinkport rethinkdb_dump_2024_01_15/myapp/
```

### Advanced Migration with Custom Configuration

```bash
rethinkport \
  rethinkdb_dump_2024_01_15/myapp/ \
  --config production_config.json \
  --batch-size 5000 \
  --dry-run
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   ```
   Error: Failed to connect to MySQL
   ```
   - Check MySQL credentials and connection
   - Ensure MySQL server is running
   - Verify database exists

2. **Large Dataset Timeouts**
   ```
   Error: MySQL server has gone away
   ```
   - Increase `max_allowed_packet` in MySQL
   - Reduce `--batch-size`
   - Check MySQL timeout settings

3. **Schema Conflicts**
   ```
   Error: Table already exists
   ```
   - Tool drops existing tables by default
   - Check MySQL user permissions
   - Verify database name

### Performance Tips

- Use SSD storage for better I/O performance
- Increase MySQL `innodb_buffer_pool_size`
- Adjust `--batch-size` based on available memory
- Run migration during low-traffic periods

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/rethinkdb-mysql-migrator.git
cd rethinkdb-mysql-migrator
pip install -e ".[dev]"
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built to solve real-world RethinkDB migration challenges
- Inspired by the need for reliable database migration tools
- Thanks to the RethinkDB and MySQL communities

## Support

If you encounter issues or have questions:

1. Check the [Issues](https://github.com/yourusername/rethinkdb-mysql-migrator/issues) page
2. Create a new issue with detailed information
3. Include your RethinkDB/MySQL versions and error logs

---

**Note**: This tool was created because existing migration solutions were insufficient for complex RethinkDB to MySQL migrations. It's designed to handle real-world scenarios with large datasets, complex schemas, and foreign key relationships.
