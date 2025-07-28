"""
RethinkPort 🚢

Port your RethinkDB data to MySQL.
A comprehensive tool for migrating RethinkDB databases to MySQL,
designed to work with official RethinkDB dump files.
"""

__version__ = "1.0.4"
__author__ = "Akeem Amusat"
__email__ = "hello@a4m.dev"

from .migrator import RethinkDBMigrator

__all__ = ["RethinkDBMigrator"]
