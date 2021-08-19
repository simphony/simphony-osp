"""Test the Sqlite Wrapper with the CITY ontology."""

import os
import unittest2 as unittest
import shutil
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
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city

DB_TEMPLATE = str(Path(__file__).parent / "test_sqlite_migration_template.db")
DB = str(Path(__file__).parent / "test_sqlite_migration.db")


class TestSqliteCity(unittest.TestCase):
    """Test the sqlite wrapper with the city ontology."""

    def tearDown(self):
        """Remove the database file."""
        if os.path.exists(DB):
            os.remove(DB)

    def run_migration(self, schema_version):
        """Run the migration."""
        shutil.copy(DB_TEMPLATE, DB)

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
            self.assertEqual(len(cities), 1)
            c = cities[0]
            self.assertTrue(c.is_a(city.City))
            self.assertEqual(c.name, "Freiburg")
            self.assertEqual(c.uid.data.hex,
                             "affb72ee61754028bd7e39a92ba3bb77")
            self.assertEqual(c.get(rel=city.isPartOf), [w])
            self.assertEqual(c.coordinates, np.array([42, 12]))

            neighborhoods = c.get(oclass=city.Neighborhood)
            n = neighborhoods[0]
            self.assertEqual(len(neighborhoods), 1)
            self.assertEqual(n.uid.data.hex,
                             "e30e0287f52b49f396b939a85fc9460d")
            self.assertEqual(n.name, "Zähringen")
            self.assertEqual(n.get(rel=city.isPartOf), [c])
            self.assertEqual(n.coordinates, np.array([0, 0]))

            streets = n.get()
            s = streets[0]
            self.assertEqual(len(streets), 1)
            self.assertEqual(s.uid.data.hex,
                             "25cb6116e9d04ceb81cdd8cfcbead47b")
            self.assertEqual(s.name, "Le street")
            self.assertEqual(s.get(rel=city.isPartOf), [n])
            self.assertEqual(s.coordinates, np.array([1, 98]))

            citizen = c.get(rel=city.hasInhabitant)
            citizen = sorted(citizen, key=lambda p: p.name)
            self.assertEqual([p.name for p in citizen],
                             ["Hans", "Michel", "Peter"])
            for p in citizen:
                self.assertEqual(p.get(rel=city.hasInhabitant.inverse), [c])
                self.assertEqual(p.get(), [])

    def test_migrate_v0(self):
        """Test migration from v1 to v2."""
        self.run_migration(1)
        self.run_test()


if __name__ == '__main__':
    unittest.main()
