# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sys
import time
import subprocess
from cuds.session.transport.transport_session_client import \
    TransportSessionClient
from cuds.session.transport.transport_session_server import \
    TransportSessionServer
from cuds.testing.test_sim_wrapper_city import DummySimSession
import cuds.classes
import unittest2 as unittest

HOST = "127.0.0.1"
PORT = 8689
TABLE = "transport.db"

SERVER_STARTED = False


class TestTransportSimWrapperCity(unittest.TestCase):

    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        args = ["python3",
                "cuds/testing/test_transport_sim_wrapper.py",
                "server"]
        try:
            p = subprocess.Popen(args)
        except FileNotFoundError:
            args[0] = "python"
            p = subprocess.Popen(args)

        TestTransportSimWrapperCity.SERVER_STARTED = p
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        TestTransportSimWrapperCity.SERVER_STARTED.terminate()

    def test_dummy_sim_wrapper(self):
        """Create a dummy simulation syntactic layer + test
        if working with this layer works as expected.
        """
        with TransportSessionClient(DummySimSession, HOST, PORT) as session:
            wrapper = cuds.classes.CitySimWrapper(num_steps=1, session=session)
            c = cuds.classes.City(name="Freiburg")
            p1 = cuds.classes.Person(name="Hans", age=34)
            p2 = cuds.classes.Person(name="Renate", age=54)
            cw, _, _ = wrapper.add(c, p1, p2)

            session.run()

            self.assertEqual(len(
                wrapper.get(cuba_key=cuds.classes.Person.cuba_key,
                            rel=cuds.classes.HasPart)), 1)
            self.assertEqual(len(
                cw.get(cuba_key=cuds.classes.Citizen.cuba_key,
                       rel=cuds.classes.HasInhabitant)), 1)
            self.assertEqual(wrapper.get(p2.uid).name, "Renate")
            self.assertEqual(wrapper.get(p2.uid).age, 55)
            self.assertEqual(cw.get(p1.uid).name, "Hans")
            self.assertEqual(cw.get(p1.uid).age, 35)

            session.run()
            wrapper.add(cuds.classes.Person(name="Peter"))
            self.assertRaises(RuntimeError, session.run)


if __name__ == '__main__':
    if sys.argv[-1] == "server":
        server = TransportSessionServer(DummySimSession, HOST, PORT)
        server.startListening()
