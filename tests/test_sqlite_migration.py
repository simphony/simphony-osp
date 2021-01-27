"""Test the Sqlite Wrapper with the CITY ontology."""

import os
import unittest2 as unittest
import sqlite3
import numpy as np
from pathlib import Path
from osp.core.session.db.sql_migrate import check_supported_schema_version, \
    detect_current_schema_version, versions
from osp.core.session.db.sql_migrate import SqlMigrate
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
        os.remove(DB)

    def run_migration(self, schema_version):
        """Load the data from the given schema version + run the migration."""
        filename = f"sqlite_schema_v{schema_version}.sql"
        with open(Path(__file__).parent / filename, encoding="utf-8") as f:
            with sqlite3.connect(DB) as con:
                con.executescript(f.read())

        self.assertRaises(RuntimeError, check_supported_schema_version,
                          SqliteSession(DB))
        self.assertRaises(RuntimeError, city.CityWrapper,
                          session=SqliteSession(DB))
        self.assertEqual(detect_current_schema_version(
            SqliteSession(DB)._get_table_names("")), schema_version
        )

        with SqliteSession(DB) as session:
            m = SqlMigrate(session)
            m.run()
            self.assertEqual(detect_current_schema_version(
                SqliteSession(DB)._get_table_names("")), max(versions.values())
            )
            self.assertTrue(check_supported_schema_version(SqliteSession(DB)))

    def run_test(self):
        """Test whether all data can be loaded correctly."""
        with SqliteSession(DB) as session:
            w = city.CityWrapper(session=session)
            cities = w.get(rel=city.hasPart)
            c = cities[0]
            self.assertEqual(len(cities), 1)
            self.assertTrue(c.is_a(city.City))
            self.assertEqual(c.name, "Freiburg")
            self.assertEqual(c.uid.hex, "affb72ee61754028bd7e39a92ba3bb77")
            self.assertEqual(c.get(rel=city.isPartOf), [w])
            np.testing.assert_equal(c.coordinates, np.array([42, 12]))

            neighborhoods = c.get(oclass=city.Neighborhood)
            n = neighborhoods[0]
            self.assertEqual(len(neighborhoods), 1)
            self.assertEqual(n.uid.hex, "e30e0287f52b49f396b939a85fc9460d")
            self.assertEqual(n.name, "Zähringen")
            self.assertEqual(n.get(rel=city.isPartOf), [c])
            np.testing.assert_equal(n.coordinates, np.array([0, 0]))

            streets = n.get()
            s = streets[0]
            self.assertEqual(len(streets), 1)
            self.assertEqual(s.uid.hex, "25cb6116e9d04ceb81cdd8cfcbead47b")
            self.assertEqual(s.name, "Le street")
            self.assertEqual(s.get(rel=city.isPartOf), [n])
            np.testing.assert_equal(s.coordinates, np.array([1, 98]))

            citizen = c.get(rel=city.hasInhabitant)
            citizen = sorted(citizen, key=lambda p: p.name)
            self.assertEqual([p.name for p in citizen],
                             ["Hans", "Michel", "Peter"])
            for p in citizen:
                self.assertEqual(p.get(rel=city.hasInhabitant.inverse), [c])
                self.assertEqual(p.get(), [])

    def test_migrate_v0(self):
        """Test migration from schema from v0."""
        # load old schema and run migratio

        # connect to db and check if
        self.run_migration(0)
        self.run_test()


if __name__ == '__main__':
    unittest.main()
