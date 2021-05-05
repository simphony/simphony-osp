"""Test the dataspace wrapper."""

import os
import sys
import subprocess
import unittest2 as unittest
import sqlite3
import logging
import time
from osp.wrappers.sqlite import SqliteSession
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.wrappers.dataspace import DataspaceSession
from osp.core.session import DbWrapperSession
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
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city

HOST = "127.0.0.1"
PORT = 8681
URI = f"ws://{HOST}:{PORT}"
DB = "dataspace.db"


class TestDataspaceWrapper(unittest.TestCase):
    """Test the DataspaceWrapper."""

    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        """Set up the server as a subprocess."""
        args = ["python",
                "tests/test_dataspace_wrapper.py",
                "server"]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)

        TestDataspaceWrapper.SERVER_STARTED = p
        for line in p.stdout:
            if b"ready" in line:
                time.sleep(0.1)
                break

    @classmethod
    def tearDownClass(cls):
        """Remove the database file."""
        TestDataspaceWrapper.SERVER_STARTED.terminate()
        os.remove(DB)

    def tearDown(self):
        """Clear the database."""
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

        with DataspaceSession(URI) as session:
            wrapper = city.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_update(self):
        """Test updating the sqlite table."""
        c = city.City(name="Paris")
        p1 = city.Citizen(name="Peter")
        c.add(p1, rel=city.hasInhabitant)

        with DataspaceSession(URI) as session:
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

        with DataspaceSession(URI) as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_user_parameterize(self):
        """Test parameterizing the dataspace as a client."""
        with TransportSessionClient(
            DbWrapperSession,
            URI, path="dataspace.db"
        ) as session:
            self.assertRaises(RuntimeError, city.CityWrapper, session=session)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        logging.getLogger(
            "osp.core.session.transport.transport_session_server"
        ).addFilter(lambda record: False)
        server = TransportSessionServer(
            SqliteSession, HOST, PORT, session_kwargs={
                "path": DB
            })
        print("ready", flush=True)
        server.startListening()
    else:
        unittest.main()
