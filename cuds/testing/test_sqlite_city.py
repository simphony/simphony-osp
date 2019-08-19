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
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen("Peter")
        p2 = cuds.classes.Citizen("Georg")
        c.add(p1, p2)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            wrapper.add(c)
            session.commit()

        self._check_state(c, p1, p2)

    def test_update(self):
        c = cuds.classes.City("Paris")
        p1 = cuds.classes.Citizen("Peter")
        c.add(p1)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            wrapper.add(c)
            session.commit()

            cw, = wrapper.get(c.uid)
            p2 = cuds.classes.Citizen("Georg")
            cw.add(p2)
            cw.name = "Freiburg"
            session.commit()

        self._check_state(c, p1, p2)

    def test_delete(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen("Peter")
        p2 = cuds.classes.Citizen("Georg")
        p3 = cuds.classes.Citizen("Hans")
        c.add(p1, p2, p3)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session)
            wrapper.add(c)
            session.commit()

            cw, = wrapper.get(c.uid)
            cw.remove(p3.uid)
            session.prune()
            session.commit()

        self._check_state(c, p1, p2)

    def _check_state(self, c, p1, p2):
        with sqlite3.connect("test.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uid, cuba, first_level FROM %s;"
                           % SqliteWrapperSession.master_table)
            result = set(cursor.fetchall())
            self.assertEqual(result, {
                (str(c.uid), c.cuba_key.value, 1),
                (str(p1.uid), p1.cuba_key.value, 0),
                (str(p2.uid), p2.cuba_key.value, 0)
            })

            cursor.execute("SELECT origin, target, name, cuba FROM %s;"
                           % SqliteWrapperSession.relationships_table)
            result = set(cursor.fetchall())
            self.assertEqual(result, {
                (str(c.uid), str(p1.uid), "HAS_PART", "CITIZEN"),
                (str(c.uid), str(p2.uid), "HAS_PART", "CITIZEN"),
                (str(p1.uid), str(c.uid), "IS_PART_OF", "CITY"),
                (str(p2.uid), str(c.uid), "IS_PART_OF", "CITY"),
                (str(c.uid), str(uuid.UUID(int=0)),
                    "IS_PART_OF", "CITY_WRAPPER")
            })

            cursor.execute("SELECT uid, name FROM CITY;")
            result = set(cursor.fetchall())
            self.assertEqual(result, {
                (str(c.uid), "Freiburg")
            })

    def test_init(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen("Peter")
        p2 = cuds.classes.Citizen("Anna")
        p3 = cuds.classes.Citizen("Julia")
        c.add(p1, p2)
        p1.add(p3)
        p2.add(p3)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid)[0].name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)[cuds.classes.HasPart],
                {p1.uid: p1.cuba_key, p2.uid: p2.cuba_key})
            self.assertEqual(
                session._registry.get(c.uid)[cuds.classes.IsPartOf],
                {wrapper.uid: wrapper.cuba_key})

    def test_load_missing(self):
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen("Peter")
        p2 = cuds.classes.Citizen("Anna")
        p3 = cuds.classes.Citizen("Julia")
        c.add(p1, p2)
        p1.add(p3)
        p2.add(p3)

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteWrapperSession("test.db") as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            cw = wrapper.get(c.uid)[0]
            p1w = cw.get(p1.uid)[0]
            p2w = cw.get(p2.uid)[0]
            p3w = p1w.get(p3.uid)[0]
            self.assertEqual(set(session._registry.keys()),
                    {c.uid, wrapper.uid, p1.uid, p2.uid, p3.uid})
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(p3w.name, "Julia")
            self.assertEqual(
                p3w[cuds.classes.IsPartOf],
                {p1.uid: p1.cuba_key, p2.uid: p2.cuba_key}
            )
            self.assertEqual(
                p2w[cuds.classes.HasPart],
                {p3.uid: p3.cuba_key}
            )
            self.assertEqual(
                p2w[cuds.classes.IsPartOf],
                {c.uid: c.cuba_key}
            )


if __name__ == '__main__':
    unittest.main()
