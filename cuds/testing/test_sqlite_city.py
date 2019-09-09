# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import uuid
import unittest2 as unittest
import cuds.classes
import sqlite3
from cuds.classes.core.session.db.sqlite_wrapper_session import \
    SqliteWrapperSession


class TestSqliteCity(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        os.remove("test.db")

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = cuds.classes.City(name="Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Georg")
        c.add(p1, p2, rel=cuds.classes.HasInhabitant)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2)

    def test_update(self):
        """Test updating the sqlite table."""
        c = cuds.classes.City("Paris")
        p1 = cuds.classes.Citizen(name="Peter")
        c.add(p1, rel=cuds.classes.HasInhabitant)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            cw = wrapper.add(c)
            session.commit()

            p2 = cuds.classes.Citizen(name="Georg")
            cw.add(p2, rel=cuds.classes.HasInhabitant)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2)

    def test_delete(self):
        """Test to delete cuds objects from the sqlite table"""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Georg")
        p3 = cuds.classes.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2)

    def test_init(self):
        """Test of first level of children are loaded automatically."""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)[cuds.classes.HasInhabitant],
                {p1.uid: p1.cuba_key, p2.uid: p2.cuba_key,
                 p3.uid: p3.cuba_key})
            self.assertEqual(
                session._registry.get(c.uid)[cuds.classes.IsPartOf],
                {wrapper.uid: wrapper.cuba_key})

    def test_load_missing(self):
        """Test if missing objects are loaded automatically."""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            cw = wrapper.get(c.uid)
            p1w = cw.get(p1.uid)
            p2w = cw.get(p2.uid)
            p3w = p1w.get(p3.uid)
            self.assertEqual(
                set(session._registry.keys()),
                {c.uid, wrapper.uid, p1.uid, p2.uid, p3.uid})
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(p3w.name, "Julia")
            self.assertEqual(
                p3w[cuds.classes.IsChildOf],
                {p1.uid: p1.cuba_key, p2.uid: p2.cuba_key}
            )
            self.assertEqual(
                p2w[cuds.classes.HasChild],
                {p3.uid: p3.cuba_key}
            )
            self.assertEqual(
                p2w[cuds.classes.IsInhabitantOf],
                {c.uid: c.cuba_key}
            )

    def test_load_by_cuba_key(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_cuba_key(cuds.classes.City.cuba_key)
            self.assertIs(next(r), cs)
            r = session.load_by_cuba_key(cuds.classes.Citizen.cuba_key)
            self.assertEqual(set(r), {p1, p2, p3})

    def test_expiring(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w = cw.get(p1.uid)
            session.commit()

            self.assertEqual(p1w.name, "Peter")

            with sqlite3.connect("test.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE CUDS_CITY SET name = 'Paris' "
                               "WHERE uid='%s';" % (c.uid))
                cursor.execute("UPDATE CUDS_CITIZEN SET name = 'Maria' "
                               "WHERE uid='%s';" % (p1.uid))
                conn.commit()

            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Peter")
            session.expire_all()
            self.assertEqual(p1w.name, "Maria")

        # TODO test if relationships have been refreshed


def check_state(test_case, c, p1, p2, table="test.db"):
    """Check if the sqlite tables are in the correct state."""
    with sqlite3.connect(table) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT uid, cuba, first_level FROM %s;"
                       % SqliteWrapperSession.MASTER_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), c.cuba_key.value, 1),
            (str(p1.uid), p1.cuba_key.value, 0),
            (str(p2.uid), p2.cuba_key.value, 0)
        })

        cursor.execute("SELECT origin, target, name, target_cuba FROM %s;"
                       % SqliteWrapperSession.RELATIONSHIP_TABLE)
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), str(p1.uid), "HAS_INHABITANT", "CITIZEN"),
            (str(c.uid), str(p2.uid), "HAS_INHABITANT", "CITIZEN"),
            (str(p1.uid), str(c.uid), "IS_INHABITANT_OF", "CITY"),
            (str(p2.uid), str(c.uid), "IS_INHABITANT_OF", "CITY"),
            (str(c.uid), str(uuid.UUID(int=0)),
                "IS_PART_OF", "CITY_WRAPPER")
        })

        cursor.execute("SELECT uid, name FROM CUDS_CITY;")
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), "Freiburg")
        })


if __name__ == '__main__':
    unittest.main()
