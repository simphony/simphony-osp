"""Test the Sqlite Wrapper with the CITY ontology."""

import os
import uuid
import unittest2 as unittest
import sqlite3
from osp.wrappers.sqlite import SqliteSession

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

DB = "test_sqlite.db"


class TestSqliteCity(unittest.TestCase):
    """Test the sqlite wrapper with the city ontology."""

    def tearDown(self):
        """Remove the database file."""
        if os.path.exists(DB):
            os.remove(DB)

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        c.add(p1, p2, rel=city.hasInhabitant)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            wrapper.session.commit()

        # check_state(self, c, p1, p2)  TODO

    def test_update(self):
        """Test updating the sqlite table."""
        c = city.City(name="Paris")
        p1 = city.Citizen(name="Peter")
        c.add(p1, rel=city.hasInhabitant)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            p2 = city.Citizen(name="Georg")
            cw.add(p2, rel=city.hasInhabitant)
            cw.name = "Freiburg"
            session.commit()

#         check_state(self, c, p1, p2)  TODO

    def test_delete(self):
        """Test to delete cuds_objects from the sqlite table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        p3 = city.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=city.hasInhabitant)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

#         check_state(self, c, p1, p2)

    def test_init(self):
        """Test of first level of children are loaded automatically."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})
            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.hasInhabitant],
                {p1.uid: p1.oclass, p2.uid: p2.oclass,
                 p3.uid: p3.oclass})
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.isPartOf],
                {wrapper.uid: wrapper.oclass})

    def test_load_missing(self):
        """Test if missing objects are loaded automatically."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
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
                p3w._neighbors[city.isChildOf],
                {p1.uid: p1.oclass, p2.uid: p2.oclass}
            )
            self.assertEqual(
                p2w._neighbors[city.hasChild],
                {p3.uid: p3.oclass}
            )
            self.assertEqual(
                p2w._neighbors[city.INVERSE_OF_hasInhabitant],
                {c.uid: c.oclass}
            )

    def test_load_by_oclass(self):
        """Test loading by oclass."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.City)
            self.assertIs(next(r), cs)
            r = session.load_by_oclass(city.Citizen)
            self.assertEqual(set(r), {p1, p2, p3})
            r = session.load_by_oclass(city.Person)
            self.assertEqual(set(r), {p1, p2, p3})

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.Street)
            self.assertRaises(StopIteration, next, r)

    def test_expiring(self):
        """Test expring CUDS objects."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            # p1w is no longer expired after the following assert
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")

            # with sqlite3.connect(DB) as conn:
            #     cursor = conn.cursor()
            #     cursor.execute("UPDATE CUDS_city___city SET name = 'Paris' "
            #                    "WHERE uid='%s';" % (c.uid))
            #     cursor.execute("UPDATE CUDS_city___Citizen SET name = 'Maria' "
            #                    "WHERE uid='%s';" % (p1.uid))
            #     cursor.execute("UPDATE CUDS_city___Citizen SET name = 'Jacob' "
            #                    "WHERE uid='%s';" % (p2.uid))
            #     cursor.execute("DELETE FROM %s "
            #                    "WHERE origin == '%s' OR target = '%s'"
            #                    % (session.RELATIONSHIP_TABLE, p2.uid, p2.uid))
            #     cursor.execute("DELETE FROM %s "
            #                    "WHERE origin == '%s' OR target = '%s'"
            #                    % (session.RELATIONSHIP_TABLE, p3.uid, p3.uid))
            #     cursor.execute("DELETE FROM CUDS_city___Citizen "
            #                    "WHERE uid == '%s'"
            #                    % p3.uid)
            #     cursor.execute("DELETE FROM %s "
            #                    "WHERE uid == '%s'"
            #                    % (session.MASTER_TABLE, p3.uid))
            #     conn.commit()

            # self.assertEqual(p2w.name, "Anna")
            # self.assertEqual(cw.name, "Paris")  # expires outdated neighbor p2w
            # self.assertEqual(p2w.name, "Jacob")
            # self.assertEqual(p1w.name, "Peter")
            # session.expire_all()
            # self.assertEqual(p1w.name, "Maria")
            # self.assertEqual(set(cw.get()), {p1w})
            # self.assertEqual(p2w.get(), list())
            # self.assertFalse(hasattr(p3w, "name"))
            # self.assertNotIn(p3w.uid, session._registry)

    def test_refresh(self):
        """Test refreshing CUDS objects."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            self.assertEqual(cw.name, "Freiburg")
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(p3w.name, "Julia")
            self.assertEqual(session._expired, {wrapper.uid})

            # with sqlite3.connect(DB) as conn:
            #     cursor = conn.cursor()
            #     cursor.execute("UPDATE CUDS_city___city SET name = 'Paris' "
            #                    "WHERE uid='%s';" % (c.uid))
            #     cursor.execute("UPDATE CUDS_city___Citizen SET name = 'Maria' "
            #                    "WHERE uid='%s';" % (p1.uid))
            #     cursor.execute("DELETE FROM %s "
            #                    "WHERE origin == '%s' OR target = '%s'"
            #                    % (session.RELATIONSHIP_TABLE, p2.uid, p2.uid))
            #     cursor.execute("DELETE FROM %s "
            #                    "WHERE origin == '%s' OR target = '%s'"
            #                    % (session.RELATIONSHIP_TABLE, p3.uid, p3.uid))
            #     cursor.execute("DELETE FROM CUDS_city___Citizen "
            #                    "WHERE uid == '%s'"
            #                    % p3.uid)
            #     cursor.execute("DELETE FROM %s "
            #                    "WHERE uid == '%s'"
            #                    % (session.MASTER_TABLE, p3.uid))
            # #     conn.commit()

            # session.refresh(cw, p1w, p2w, p3w)
            # self.assertEqual(cw.name, "Paris")
            # self.assertEqual(p1w.name, "Maria")
            # self.assertEqual(set(cw.get()), {p1w})
            # self.assertEqual(p2w.get(), list())
            # self.assertFalse(hasattr(p3w, "name"))
            # self.assertNotIn(p3w.uid, session._registry)

#     def test_clear_database(self):
#         """Test clearing the database."""
#         # db is empty (no error occurs)
#         with SqliteSession(DB) as session:
#             wrapper = city.CityWrapper(session=session)
#             session._clear_database()
#         with SqliteSession(DB) as session:
#             wrapper = city.CityWrapper(session=session)
#             wrapper.session.commit()
#             session._clear_database()

#         # db is not empty
#         c = city.City(name="Freiburg")
#         p1 = city.Citizen(name="Peter")
#         p2 = city.Citizen(name="Anna")
#         p3 = city.Citizen(name="Julia")
#         c.add(p1, p2, p3, rel=city.hasInhabitant)
#         p1.add(p3, rel=city.hasChild)
#         p2.add(p3, rel=city.hasChild)

#         with SqliteSession(DB) as session:
#             wrapper = city.CityWrapper(session=session)
#             wrapper.add(c)
#             session.commit()
#             session._clear_database()

#         check_db_cleared(self, DB)

#     def test__sql_list_pattern(self):
#         """Test transformation of value lists to SQLite patterns."""
#         p, v = SqliteSession._sql_list_pattern("pre", [42, "yo", 1.2, "hey"])
#         self.assertEqual(p, ":pre_0, :pre_1, :pre_2, :pre_3")
#         self.assertEqual(v, {
#             "pre_0": 42,
#             "pre_1": "yo",
#             "pre_2": 1.2,
#             "pre_3": "hey"
#         })

#     def test_multiple_users(self):
#         """Test what happens if multiple users access the database."""
#         with SqliteSession(DB) as session1:
#             wrapper1 = city.CityWrapper(session=session1)
#             city1 = city.City(name="Freiburg")
#             wrapper1.add(city1)
#             session1.commit()

#             with SqliteSession(DB) as session2:
#                 wrapper2 = city.CityWrapper(session=session2)
#                 wrapper2.add(city.City(name="Offenburg"))
#                 session2.commit()

#                 cw = wrapper1.add(city.City(name="Karlsruhe"))
#                 self.assertEqual(session1._expired, set())
#                 self.assertEqual(session1._buffers, [
#                     [{cw.uid: cw}, {wrapper1.uid: wrapper1}, dict()],
#                     [dict(), dict(), dict()]
#                 ])
#                 session1.commit()


# def check_state(test_case, c, p1, p2, db=DB):
#     """Check if the sqlite tables are in the correct state."""
#     with sqlite3.connect(db) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT uid, oclass, first_level FROM %s;"
#                        % SqliteSession.MASTER_TABLE)
#         result = set(cursor.fetchall())
#         test_case.assertEqual(result, {
#             (str(uuid.UUID(int=0)), "", 0),
#             (str(c.uid), str(c.oclass), 1),
#             (str(p1.uid), str(p1.oclass), 0),
#             (str(p2.uid), str(p2.oclass), 0)
#         })

#         cursor.execute("SELECT origin, target, name, target_oclass FROM %s;"
#                        % SqliteSession.RELATIONSHIP_TABLE)
#         result = set(cursor.fetchall())
#         test_case.assertEqual(result, {
#             (str(c.uid), str(p1.uid), "city.hasInhabitant", "city.Citizen"),
#             (str(c.uid), str(p2.uid), "city.hasInhabitant", "city.Citizen"),
#             (str(p1.uid), str(c.uid),
#              "city.INVERSE_OF_hasInhabitant", "city.City"),
#             (str(p2.uid), str(c.uid),
#              "city.INVERSE_OF_hasInhabitant", "city.City"),
#             (str(c.uid), str(uuid.UUID(int=0)),
#                 "city.isPartOf", "city.CityWrapper")
#         })

#         cursor.execute("SELECT uid, name, coordinates___0, coordinates___1 "
#                        "FROM CUDS_city___City;")
#         result = set(cursor.fetchall())
#         test_case.assertEqual(result, {
#             (str(c.uid), "Freiburg", 0, 0)
#         })


# def check_db_cleared(test_case, table):
#     """Check whether the database has been cleared successfully."""
#     with sqlite3.connect(table) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM %s;"
#                        % SqliteSession.MASTER_TABLE)
#         test_case.assertEqual(
#             list(cursor), [('00000000-0000-0000-0000-000000000000', '', 0)])
#         cursor.execute("SELECT * FROM %s;"
#                        % SqliteSession.RELATIONSHIP_TABLE)
#         test_case.assertEqual(list(cursor), list())
#         cursor.execute("SELECT * FROM CUDS_city___Citizen")
#         test_case.assertEqual(list(cursor), list())
#         cursor.execute("SELECT * FROM CUDS_city___city")
#         test_case.assertEqual(list(cursor), list())


if __name__ == '__main__':
    unittest.main()
