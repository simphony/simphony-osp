import os
import sys
import time
import subprocess
import unittest2 as unittest
import sqlite3
from osp.wrappers.sqlite import SqliteSession
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer

try:
    from tests.test_sqlite_city import check_state
except ImportError:
    from test_sqlite_city import check_state

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    from osp.core.namespaces import city

HOST = "127.0.0.1"
PORT = 8687
URI = f"ws://{HOST}:{PORT}"
DB = "transport.db"


class TestTransportSqliteCity(unittest.TestCase):
    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        args = ["python",
                "tests/test_transport_sqlite_city.py",
                "server"]
        p = subprocess.Popen(args)

        TestTransportSqliteCity.SERVER_STARTED = p
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        TestTransportSqliteCity.SERVER_STARTED.terminate()
        os.remove(DB)

    def tearDown(self):
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            tables = c.execute("SELECT name FROM sqlite_master "
                               + "WHERE type='table';")
            tables = list(tables)
            for table in tables:
                c.execute("DELETE FROM %s;" % table[0])
            conn.commit()

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        c.add(p1, p2, rel=city.hasInhabitant)

        with TransportSessionClient(SqliteSession, URI, path=DB) \
                as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_update(self):
        """Test updating the sqlite table."""
        c = city.City(name="Paris")
        p1 = city.Citizen(name="Peter")
        c.add(p1, rel=city.hasInhabitant)

        with TransportSessionClient(SqliteSession, URI, path=DB) \
                as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            p2 = city.Citizen(name="Georg")
            cw.add(p2, rel=city.hasInhabitant)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_delete(self):
        """Test to delete cuds_objects from the sqlite table"""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        p3 = city.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=city.hasInhabitant)

        with TransportSessionClient(SqliteSession, URI, path=DB) \
                as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_init(self):
        """Test if first level of children are loaded automatically."""
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

        with TransportSessionClient(SqliteSession, URI, path=DB) \
                as session:
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

        with TransportSessionClient(SqliteSession, URI, path=DB) \
                as session:
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
                p2w._neighbors[city.isInhabitantOf],
                {c.uid: c.oclass}
            )

    def test_expiring(self):
        """Test expiring with transport + db session"""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with TransportSessionClient(SqliteSession, URI, path=DB)\
                as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            # p1w is no longer expired after the following assert
            self.assertEqual(p1w.name, "Peter")

            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE CUDS_city___city SET name = 'Paris' "
                               "WHERE uid='%s';" % (c.uid))
                cursor.execute("UPDATE CUDS_city___CITIZEN SET name = 'Maria' "
                               "WHERE uid='%s';" % (p1.uid))
                cursor.execute("DELETE FROM %s "
                               "WHERE origin == '%s' OR target = '%s'"
                               % (SqliteSession.RELATIONSHIP_TABLE,
                                  p2.uid, p2.uid))
                cursor.execute("DELETE FROM %s "
                               "WHERE origin == '%s' OR target = '%s'"
                               % (SqliteSession.RELATIONSHIP_TABLE,
                                  p3.uid, p3.uid))
                cursor.execute("DELETE FROM CUDS_city___CITIZEN "
                               "WHERE uid == '%s'"
                               % p3.uid)
                cursor.execute("DELETE FROM %s "
                               "WHERE uid == '%s'"
                               % (SqliteSession.MASTER_TABLE, p3.uid))
                conn.commit()

            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Peter")
            session.expire_all()
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)

    def test_load_by_oclass(self):
        """Load elements by ontology class via transport + db session"""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with TransportSessionClient(SqliteSession, URI, path=DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with TransportSessionClient(SqliteSession, URI, path=DB) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.City)
            self.assertIs(next(iter(r)), cs)
            r = session.load_by_oclass(city.Citizen)
            self.assertEqual(set(r), {p1, p2, p3})
            r = session.load_by_oclass(city.Person)
            self.assertEqual(set(r), {p1, p2, p3})

    def test_refresh(self):
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with TransportSessionClient(SqliteSession, URI, path=DB) \
                as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            self.assertEqual(cw.name, "Freiburg")
            self.assertEqual(p1w.name, "Peter")
            self.assertEqual(p2w.name, "Anna")
            self.assertEqual(p3w.name, "Julia")
            self.assertEqual(session._expired, {wrapper.uid})

            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE CUDS_city___city SET name = 'Paris' "
                               "WHERE uid='%s';" % (c.uid))
                cursor.execute("UPDATE CUDS_city___CITIZEN SET name = 'Maria' "
                               "WHERE uid='%s';" % (p1.uid))
                cursor.execute("DELETE FROM %s "
                               "WHERE origin == '%s' OR target = '%s'"
                               % (SqliteSession.RELATIONSHIP_TABLE,
                                  p2.uid, p2.uid))
                cursor.execute("DELETE FROM %s "
                               "WHERE origin == '%s' OR target = '%s'"
                               % (SqliteSession.RELATIONSHIP_TABLE,
                                  p3.uid, p3.uid))
                cursor.execute("DELETE FROM CUDS_city___CITIZEN "
                               "WHERE uid == '%s'"
                               % p3.uid)
                cursor.execute("DELETE FROM %s "
                               "WHERE uid == '%s'"
                               % (SqliteSession.MASTER_TABLE, p3.uid))
                conn.commit()

            session.refresh(cw, p1w, p2w, p3w)
            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        server = TransportSessionServer(SqliteSession, HOST, PORT)
        server.startListening()
