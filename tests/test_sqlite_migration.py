"""Test the Sqlite Wrapper with the CITY ontology."""

import os
import unittest2 as unittest
import sqlite3
from pathlib import Path
from osp.wrappers.sqlite.migration import SqliteMigrate
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

    def run_migration(self, schema_version):
        """Load the data from the given schema version + run the migration."""
        filename = f"sqlite_schema_v{schema_version}.sql"
        with open(Path(__file__).parent / filename) as f:
            with sqlite3.connect(DB) as con:
                con.executescript(f.read())
        m = SqliteMigrate(DB)
        m.run()

    def run_test(self):
        """Test whether all data can be loaded correctly."""
        with SqliteSession(DB) as session:
            w = city.CityWrapper(session=session)
            w.get()

    def test_migrate_v0(self):
        """Test migration from schema from v0."""
        # load old schema and run migratio

        # connect to db and check if
        self.run_migration(0)
        self.run_test()


if __name__ == '__main__':
    unittest.main()
