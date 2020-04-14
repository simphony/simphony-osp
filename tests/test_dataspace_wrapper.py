# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import sys
import time
import subprocess
import unittest2 as unittest
import sqlite3
import logging
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
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")

HOST = "127.0.0.1"
PORT = 8681
DB = "dataspace.db"


class TestTransportSqliteCity(unittest.TestCase):
    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        args = ["python3",
                "tests/test_dataspace_wrapper.py",
                "server"]
        try:
            p = subprocess.Popen(args)
        except FileNotFoundError:
            args[0] = "python"
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
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Georg")
        c.add(p1, p2, rel=CITY.HAS_INHABITANT)

        with DataspaceSession(HOST, PORT) as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_update(self):
        """Test updating the sqlite table."""
        c = CITY.CITY(name="Paris")
        p1 = CITY.CITIZEN(name="Peter")
        c.add(p1, rel=CITY.HAS_INHABITANT)

        with DataspaceSession(HOST, PORT) as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cw = wrapper.add(c)
            session.commit()

            p2 = CITY.CITIZEN(name="Georg")
            cw.add(p2, rel=CITY.HAS_INHABITANT)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_delete(self):
        """Test to delete cuds_objects from the sqlite table"""
        c = CITY.CITY(name="Freiburg")
        p1 = CITY.CITIZEN(name="Peter")
        p2 = CITY.CITIZEN(name="Georg")
        p3 = CITY.CITIZEN(name="Hans")
        c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)

        with DataspaceSession(HOST, PORT) as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2, db=DB)

    def test_user_parameterize(self):
        """Test that parameterizing the dataspace as
        a client throws an error"""
        with TransportSessionClient(DbWrapperSession,
                                    HOST, PORT, path="test.db") as session:
            self.assertRaises(RuntimeError, CITY.CITY_WRAPPER, session=session)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        logging.getLogger(
            "osp.core.session.transport.transport_session_server"
        ).addFilter(lambda record: False)
        server = TransportSessionServer(
            SqliteSession, HOST, PORT, session_kwargs={
                "path": DB
            })
        server.startListening()
