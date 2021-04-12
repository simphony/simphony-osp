"""Test the Sqlite Wrapper with the CITY ontology."""

import os
from osp.core.utils.general import iri_from_uid
import uuid
import unittest2 as unittest
import sqlite3
import numpy as np
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

CUDS_TABLE = SqliteSession.CUDS_TABLE
ENTITIES_TABLE = SqliteSession.ENTITIES_TABLE
TYPES_TABLE = SqliteSession.TYPES_TABLE
NAMESPACES_TABLE = SqliteSession.NAMESPACES_TABLE
RELATIONSHIP_TABLE = SqliteSession.RELATIONSHIP_TABLE
DATA_TABLE_PREFIX = SqliteSession.DATA_TABLE_PREFIX


def data_tbl(suffix):
    """Prepend data table prefix."""
    return DATA_TABLE_PREFIX + suffix


class TestSqliteCity(unittest.TestCase):
    """Test the sqlite wrapper with the city ontology."""

    def tearDown(self):
        """Remove the database file."""
        if os.path.exists(DB):
            os.remove(DB)

    def test_vector(self):
        """Test capabilities to store vectors."""
        c = city.City(name="Frankfurt", coordinates=[42, 24])
        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            wrapper.session.commit()

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.get(c.uid)
            np.testing.assert_array_equal(cw.coordinates, [42, 24])

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

        check_state(self, c, p1, p2)

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

        check_state(self, c, p1, p2)

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
            session._notify_read(wrapper)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2)

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
                {p1.uid: p1.oclasses, p2.uid: p2.oclasses,
                 p3.uid: p3.oclasses})
            self.assertEqual(
                session._registry.get(c.uid)._neighbors[city.isPartOf],
                {wrapper.uid: wrapper.oclasses})

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
                {p1.uid: p1.oclasses, p2.uid: p2.oclasses}
            )
            self.assertEqual(
                p2w._neighbors[city.hasChild],
                {p3.uid: p3.oclasses}
            )
            self.assertEqual(
                p2w._neighbors[city.INVERSE_OF_hasInhabitant],
                {c.uid: c.oclasses}
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

    def test_load_by_iri(self):
        """Test if it is possible to load objects by their IRIs."""
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
            r = session.load_from_iri(cs.iri)
            self.assertIs(next(r), cs)
            r = session.load_from_iri(p1.iri, p2.iri, p3.iri)
            self.assertEqual(set(r), {p1, p2, p3})

        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_from_iri(iri_from_uid(uuid.UUID(int=1)))
            self.assertEqual(set(r), {None})

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

            update_db(DB, c, p1, p2, p3)

            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(cw.name, "Paris")  # expires outdated neighbor p2w
            self.assertEqual(p2w.name, "Jacob")
            self.assertEqual(p1w.name, "Peter")
            session.expire_all()
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)

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

            update_db(DB, c, p1, p2, p3)

            session.refresh(cw, p1w, p2w, p3w)
            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)

    def test_clear_database(self):
        """Test clearing the database."""
        # db is empty (no error occurs)
        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            session._clear_database()
        with SqliteSession(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.session.commit()
            session._clear_database()

        # db is not empty
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
            session._clear_database()

        check_db_cleared(self, DB)

    def test_sql_list_pattern(self):
        """Test transformation of value lists to SQLite patterns."""
        p, v = SqliteSession._sql_list_pattern("pre", [42, "yo", 1.2, "hey"])
        self.assertEqual(p, ":pre_0, :pre_1, :pre_2, :pre_3")
        self.assertEqual(v, {
            "pre_0": 42,
            "pre_1": "yo",
            "pre_2": 1.2,
            "pre_3": "hey"
        })

    def test_multiple_users(self):
        """Test what happens if multiple users access the database."""
        with SqliteSession(DB) as session1:
            wrapper1 = city.CityWrapper(session=session1)
            city1 = city.City(name="Freiburg")
            wrapper1.add(city1)
            session1.commit()

            with SqliteSession(DB) as session2:
                wrapper2 = city.CityWrapper(session=session2)
                wrapper2.add(city.City(name="Offenburg"))
                session2.commit()

                cw = wrapper1.add(city.City(name="Karlsruhe"))
                self.assertEqual(session1._expired, {city1.uid})
                self.assertEqual(session1._buffers, [
                    [{cw.uid: cw}, {wrapper1.uid: wrapper1}, dict()],
                    [dict(), dict(), dict()]
                ])
                session1.commit()


def check_state(test_case, c, p1, p2, db=DB):
    """Check if the sqlite tables are in the correct state."""
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';")
        result = set(map(lambda x: x[0], cursor))
        test_case.assertEqual(result, set([
            RELATIONSHIP_TABLE, data_tbl("VECTOR-INT-2"), CUDS_TABLE,
            NAMESPACES_TABLE, ENTITIES_TABLE, TYPES_TABLE,
            data_tbl("XSD_boolean"), data_tbl("XSD_float"),
            data_tbl("XSD_integer"), data_tbl("XSD_string")]))

        cursor.execute(
            "SELECT `ts`.`uid`, `tp`.`ns_idx`, `tp`.`name`, `to`.`uid` "
            "FROM `%s` AS `x`, `%s` AS `ts`, `%s` AS `tp`, `%s` AS `to` "
            "WHERE `x`.`s`=`ts`.`cuds_idx` AND `x`.`p`=`tp`.`entity_idx` "
            "AND `x`.`o`=`to`.`cuds_idx`;"
            % (RELATIONSHIP_TABLE, CUDS_TABLE,
               ENTITIES_TABLE, CUDS_TABLE))
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(uuid.UUID(int=0)), 1, "hasPart", str(c.uid)),
            (str(c.uid), 1, "hasInhabitant", str(p1.uid)),
            (str(c.uid), 1, "hasInhabitant", str(p2.uid)),
            (str(p1.uid), 1, "INVERSE_OF_hasInhabitant", str(c.uid)),
            (str(p2.uid), 1, "INVERSE_OF_hasInhabitant", str(c.uid)),
            (str(c.uid), 1, "isPartOf", str(uuid.UUID(int=0)))
        })

        cursor.execute(
            "SELECT `ns_idx`, `namespace` FROM `%s`;"
            % NAMESPACES_TABLE
        )
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (1, "http://www.osp-core.com/city#")
        })

        cursor.execute(
            "SELECT `ts`.`uid`, `to`.`ns_idx`, `to`.`name` "
            "FROM `%s` AS `x`, `%s` AS `ts`, `%s` AS `to` "
            "WHERE `x`.`s`=`ts`.`cuds_idx` AND `x`.`o`=`to`.`entity_idx`;"
            % (TYPES_TABLE, CUDS_TABLE, ENTITIES_TABLE))
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), 1, 'City'),
            (str(p1.uid), 1, 'Citizen'),
            (str(p2.uid), 1, 'Citizen'),
            (str(uuid.UUID(int=0)), 1, 'CityWrapper')
        })

        cursor.execute(
            "SELECT `ts`.`uid`, `tp`.`ns_idx`, `tp`.`name`, `x`.`o` "
            "FROM `%s` AS `x`, `%s` AS `ts`, `%s` AS `tp` "
            "WHERE `x`.`s`=`ts`.`cuds_idx` AND `x`.`p`=`tp`.`entity_idx` ;"
            % (data_tbl("XSD_string"), CUDS_TABLE, ENTITIES_TABLE))
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(p1.uid), 1, 'name', 'Peter'),
            (str(c.uid), 1, 'name', 'Freiburg'),
            (str(p2.uid), 1, 'name', 'Georg')
        })

        cursor.execute(
            "SELECT `ts`.`uid`, `tp`.`ns_idx`, `tp`.`name`, "
            "`x`.`o___0` , `x`.`o___1` "
            "FROM `%s` AS `x`, `%s` AS `ts`, `%s` AS `tp` "
            "WHERE `x`.`s`=`ts`.`cuds_idx` AND `x`.`p`=`tp`.`entity_idx` ;"
            % (data_tbl("VECTOR-INT-2"), CUDS_TABLE, ENTITIES_TABLE))
        result = set(cursor.fetchall())
        test_case.assertEqual(result, {
            (str(c.uid), 1, 'coordinates', 0, 0)
        })


def check_db_cleared(test_case, db_file):
    """Check whether the database has been cleared successfully."""
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {CUDS_TABLE};")
        test_case.assertEqual(list(cursor), list())
        cursor.execute(f"SELECT * FROM {ENTITIES_TABLE};")
        test_case.assertEqual(list(cursor), list())
        cursor.execute(f"SELECT * FROM {TYPES_TABLE};")
        test_case.assertEqual(list(cursor), list())
        cursor.execute(f"SELECT * FROM {NAMESPACES_TABLE};")
        test_case.assertEqual(list(cursor), list())
        cursor.execute(f"SELECT * FROM {RELATIONSHIP_TABLE};")
        test_case.assertEqual(list(cursor), list())

        # DATA TABLES
        with SqliteSession(DB) as s:
            table_names = s._get_table_names(DATA_TABLE_PREFIX)
        for table_name in table_names:
            cursor.execute(f"SELECT * FROM `{table_name}`;")
            test_case.assertEqual(list(cursor), list())


def update_db(db, c, p1, p2, p3):
    """Make some changes to the data in the database."""
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT `uid`, `cuds_idx` FROM {CUDS_TABLE};")
        m = dict(map(lambda x: (uuid.UUID(hex=x[0]), x[1]), cursor))
        cursor.execute(f"SELECT `name`, `entity_idx` "
                       f"FROM {ENTITIES_TABLE} ;")
        e = dict(cursor)

        cursor.execute(f"UPDATE {data_tbl('XSD_string')} SET o = 'Paris' "
                       f"WHERE s={m[c.uid]} AND p={e['name']};")
        cursor.execute(f"UPDATE {data_tbl('XSD_string')} SET o = 'Maria' "
                       f"WHERE s={m[p1.uid]} AND p={e['name']};")
        cursor.execute(f"UPDATE {data_tbl('XSD_string')} SET o = 'Jacob' "
                       f"WHERE s={m[p2.uid]} AND p={e['name']};")

        cursor.execute(f"DELETE FROM {RELATIONSHIP_TABLE} "
                       f"WHERE s == '{m[p2.uid]}' OR o = '{m[p2.uid]}'")
        cursor.execute(f"DELETE FROM {RELATIONSHIP_TABLE} "
                       f"WHERE s == '{m[p3.uid]}' OR o = '{m[p3.uid]}'")
        cursor.execute(f"DELETE FROM {data_tbl('XSD_string')} "
                       f"WHERE s == '{m[p3.uid]}'")
        cursor.execute(f"DELETE FROM '{data_tbl('XSD_integer')}' "
                       f"WHERE s == '{m[p3.uid]}'")
        cursor.execute(f"DELETE FROM {CUDS_TABLE} "
                       f"WHERE cuds_idx == '{m[p3.uid]}'")
        conn.commit()


if __name__ == '__main__':
    unittest.main()
