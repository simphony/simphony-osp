"""This file contains tests for the Sqlite Wrapper using the City ontology."""
import os
import sys
import subprocess
import unittest2 as unittest
import sqlite3
import time
from osp.wrappers.sqlite import SQLiteInterface
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer

try:
    from tests.test_sqlite_city import check_state, update_db
except ImportError:
    from test_sqlite_city import check_state, update_db

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city

HOST = "127.0.0.1"
PORT = 8687
URI = f"ws://{HOST}:{PORT}"
DB = "transport.interfaces"


class TestTransportSqliteCity(unittest.TestCase):
    """Test the sqlite wrapper."""

    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        """Set up the server as a subprocess."""
        args = ["python",
                "tests/test_transport_sqlite_city.py",
                "server"]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)

        TestTransportSqliteCity.SERVER_STARTED = p
        for line in p.stdout:
            if b"ready" in line:
                time.sleep(0.1)
                break

    @classmethod
    def tearDownClass(cls):
        """Remove DB files and shut down the server subprocess."""
        TestTransportSqliteCity.SERVER_STARTED.terminate()
        os.remove(DB)

    def tearDown(self):
        """Delete table contents."""
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            tables = c.execute("SELECT name FROM sqlite_master "
                               + "WHERE type='table';")
            tables = list(tables)
            for table in tables:
                c.execute("DELETE FROM `%s`;" % table[0])
            conn.commit()

    def test_insert(self):
        """Test inserting in the sqlite table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        c.add(p1, p2, rel=city.hasInhabitant)

        with TransportSessionClient(SQLiteInterface, URI, path=DB) \
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

        with TransportSessionClient(SQLiteInterface, URI, path=DB) \
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
        """Test to delete cuds_objects from the sqlite table."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Georg")
        p3 = city.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=city.hasInhabitant)

        with TransportSessionClient(SQLiteInterface, URI, path=DB) \
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

        with SQLiteInterface(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with TransportSessionClient(SQLiteInterface, URI, path=DB) \
                as session:
            wrapper = city.CityWrapper(session=session)
            self.assertEqual(set(session._registry.keys()),
                             {c.uid, wrapper.uid})

            self.assertEqual(wrapper.get(c.uid).name, "Freiburg")
            self.assertEqual(
                session._registry.get(c.uid)
                       ._neighbors[city.hasInhabitant],
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

        with SQLiteInterface(DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with TransportSessionClient(SQLiteInterface, URI, path=DB) \
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
                {c.uid, wrapper.uid, p1.uid,
                 p2.uid, p3.uid})
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

    def test_expiring(self):
        """Test expiring with transport + interfaces session."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with TransportSessionClient(SQLiteInterface, URI, path=DB)\
                as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            # p1w is no longer expired after the following assert
            self.assertEqual(p1w.name, "Peter")

            update_db(DB, c, p1, p2, p3)

            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Peter")
            session.expire_all()
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)

    def test_load_by_oclass(self):
        """Load elements by ontology class via transport + interfaces session."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with TransportSessionClient(SQLiteInterface, URI, path=DB) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with TransportSessionClient(SQLiteInterface, URI, path=DB) as session:
            wrapper = city.CityWrapper(session=session)
            cs = wrapper.get(c.uid)
            r = session.load_by_oclass(city.City)
            self.assertIs(next(iter(r)), cs)
            r = session.load_by_oclass(city.Citizen)
            self.assertEqual(set(r), {p1, p2, p3})
            r = session.load_by_oclass(city.Person)
            self.assertEqual(set(r), {p1, p2, p3})

    def test_refresh(self):
        """Test refreshing CUDS objects."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Peter")
        p2 = city.Citizen(name="Anna")
        p3 = city.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=city.hasInhabitant)
        p1.add(p3, rel=city.hasChild)
        p2.add(p3, rel=city.hasChild)

        with TransportSessionClient(SQLiteInterface, URI, path=DB) \
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

            update_db(DB, c, p1, p2, p3)

            session.refresh(cw, p1w, p2w, p3w)
            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertFalse(hasattr(p3w, "name"))
            self.assertNotIn(p3w.uid, session._registry)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        server = TransportSessionServer(SQLiteInterface, HOST, PORT)
        print("ready", flush=True)
        server.startListening()
    else:
        unittest.main()
