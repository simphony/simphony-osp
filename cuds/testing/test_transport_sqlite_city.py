# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sys
import unittest2 as unittest
import cuds.classes
import sqlite3
from cuds.testing.test_sqlite_city import check_state
from cuds.classes.core.session.db.sqlite_wrapper_session import \
    SqliteWrapperSession
from cuds.classes.core.session.transport.transport_session_client import \
    TransportSessionClient
from cuds.classes.core.session.transport.transport_session_server import \
    TransportSessionServer

HOST = "127.0.0.1"
PORT = 8687
TABLE = "transport.db"

SERVER_STARTED = False


class TestTransportSqliteCity(unittest.TestCase):

    def tearDown(self):
        with sqlite3.connect(TABLE) as conn:
            c = conn.cursor()
            tables = c.execute("SELECT name FROM sqlite_master "
                               + "WHERE type='table';")
            tables = list(tables)
            for table in tables:
                c.execute("DELETE FROM %s;" % table[0])
            conn.commit()

    def test_insert(self):
        """Test inserting in the sqlite table."""
        if not SERVER_STARTED:
            return
        c = cuds.classes.City(name="Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Georg")
        c.add(p1, p2, rel=cuds.classes.HasInhabitant)

        with TransportSessionClient(SqliteWrapperSession, HOST, PORT, TABLE) \
                as session:
            wrapper = cuds.classes.CityWrapper(session)
            wrapper.add(c)
            session.commit()

        check_state(self, c, p1, p2, table=TABLE)

    def test_update(self):
        """Test updating the sqlite table."""
        if not SERVER_STARTED:
            return
        c = cuds.classes.City("Paris")
        p1 = cuds.classes.Citizen(name="Peter")
        c.add(p1, rel=cuds.classes.HasInhabitant)

        with TransportSessionClient(SqliteWrapperSession, HOST, PORT, TABLE) \
                as session:
            wrapper = cuds.classes.CityWrapper(session)
            cw = wrapper.add(c)
            session.commit()

            p2 = cuds.classes.Citizen(name="Georg")
            cw.add(p2, rel=cuds.classes.HasInhabitant)
            cw.name = "Freiburg"
            session.commit()

        check_state(self, c, p1, p2, table=TABLE)

    def test_delete(self):
        """Test to delete cuds objects from the sqlite table"""
        if not SERVER_STARTED:
            return
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Georg")
        p3 = cuds.classes.Citizen(name="Hans")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)

        with TransportSessionClient(SqliteWrapperSession, HOST, PORT, TABLE) \
                as session:
            wrapper = cuds.classes.CityWrapper(session)
            cw = wrapper.add(c)
            session.commit()

            cw.remove(p3.uid)
            session.prune()
            session.commit()

        check_state(self, c, p1, p2, table=TABLE)

    def test_init(self):
        """Test if first level of children are loaded automatically."""
        if not SERVER_STARTED:
            return
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqliteWrapperSession(TABLE) as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with TransportSessionClient(SqliteWrapperSession, HOST, PORT, TABLE) \
                as session:
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
        if not SERVER_STARTED:
            return
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with SqliteWrapperSession(TABLE) as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            wrapper.add(c)
            session.commit()

        with TransportSessionClient(SqliteWrapperSession, HOST, PORT, TABLE) \
                as session:
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

    def test_expiring(self):
        if not SERVER_STARTED:
            return
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Peter")
        p2 = cuds.classes.Citizen(name="Anna")
        p3 = cuds.classes.Citizen(name="Julia")
        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)

        with TransportSessionClient(SqliteWrapperSession, HOST, PORT, TABLE)\
                as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            cw = wrapper.add(c)
            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            session.commit()

            # p1w is no longer expired after the following assert
            self.assertEqual(p1w.name, "Peter")

            with sqlite3.connect(TABLE) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE CUDS_CITY SET name = 'Paris' "
                               "WHERE uid='%s';" % (c.uid))
                cursor.execute("UPDATE CUDS_CITIZEN SET name = 'Maria' "
                               "WHERE uid='%s';" % (p1.uid))
                cursor.execute("DELETE FROM %s "
                               "WHERE origin == '%s' OR target = '%s'"
                               % (SqliteWrapperSession.RELATIONSHIP_TABLE,
                                  p2.uid, p2.uid))
                cursor.execute("DELETE FROM %s "
                               "WHERE origin == '%s' OR target = '%s'"
                               % (SqliteWrapperSession.RELATIONSHIP_TABLE,
                                  p3.uid, p3.uid))
                cursor.execute("DELETE FROM CUDS_CITIZEN "
                               "WHERE uid == '%s'"
                               % p3.uid)
                cursor.execute("DELETE FROM %s "
                               "WHERE uid == '%s'"
                               % (SqliteWrapperSession.MASTER_TABLE, p3.uid))
                conn.commit()

            self.assertEqual(cw.name, "Paris")
            self.assertEqual(p1w.name, "Peter")
            session.expire_all()
            self.assertEqual(p1w.name, "Maria")
            self.assertEqual(set(cw.get()), {p1w})
            self.assertEqual(p2w.get(), list())
            self.assertEqual(p3w.name, None)
            self.assertNotIn(p3w.uid, session._registry)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        server = TransportSessionServer(SqliteWrapperSession, HOST, PORT)
        server.startListening()
    else:
        SERVER_STARTED = True
        unittest.main()
