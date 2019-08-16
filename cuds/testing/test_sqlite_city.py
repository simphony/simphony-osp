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


if __name__ == '__main__':
    unittest.main()
