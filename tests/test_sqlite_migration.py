"""Test the Sqlite Wrapper with the CITY ontology."""

import os
import uuid
import unittest2 as unittest
import sqlite3
from pathlib import Path
from osp.wrappers.sqlite import SqliteSession

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

DB = "test_sqlite_migration.db"


class TestSqliteCity(unittest.TestCase):
    """Test the sqlite wrapper with the city ontology."""

    def tearDown(self):
        """Remove the database file."""
        if os.path.exists(DB):
            os.remove(DB)

    def test_migrate_0_1(self):
        """Test migration from schema v0 to v1."""
        with open(Path(__file__).parent / "sqlite_schema_v1.sql") as f:
            with sqlite3.connect(DB) as con:
                con.executescript(f.read())
        input("ok?")


if __name__ == '__main__':
    unittest.main()
