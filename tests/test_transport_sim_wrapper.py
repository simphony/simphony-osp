"""This file contains tests for the transport session."""

import logging
import subprocess
import sys
import time

import unittest2 as unittest

from osp.core.session.transport.transport_session_client import (
    TransportSessionClient,
)
from osp.core.session.transport.transport_session_server import (
    TransportSessionServer,
)
from osp.wrappers.simdummy import SimDummySession

logger = logging.getLogger("osp.core")
logger.setLevel(logging.CRITICAL)

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry

    Parser().parse("city")
    city = namespace_registry.city

HOST = "127.0.0.1"
PORT = 8689
URI = f"ws://{HOST}:{PORT}"
TABLE = "transport.db"

SERVER_STARTED = False


class TestTransportSimWrapperCity(unittest.TestCase):
    """Test the transport session with a simulation session."""

    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        """Set up the server as a subprocess."""
        args = ["python", "tests/test_transport_sim_wrapper.py", "server"]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)

        TestTransportSimWrapperCity.SERVER_STARTED = p
        for line in p.stdout:
            if b"ready" in line:
                time.sleep(0.1)
                break

    @classmethod
    def tearDownClass(cls):
        """Shut down the server subprocess."""
        TestTransportSimWrapperCity.SERVER_STARTED.terminate()

    def test_dummy_sim_wrapper(self):
        """Create a dummy simulation syntactic layer + test it."""
        with TransportSessionClient(SimDummySession, URI) as session:
            wrapper = city.CitySimWrapper(numSteps=1, session=session)
            c = city.City(name="Freiburg")
            p1 = city.Person(name="Hans", age=34)
            p2 = city.Person(name="Renate", age=54)
            cw, _, _ = wrapper.add(c, p1, p2)

            session.run()

            self.assertEqual(
                len(wrapper.get(oclass=city.Person, rel=city.hasPart)), 1
            )
            self.assertEqual(
                len(cw.get(oclass=city.Citizen, rel=city.hasInhabitant)), 1
            )
            self.assertEqual(wrapper.get(p2.uid).name, "Renate")
            self.assertEqual(wrapper.get(p2.uid).age, 55)
            self.assertEqual(cw.get(p1.uid).name, "Hans")
            self.assertEqual(cw.get(p1.uid).age, 35)

            session.run()
            wrapper.add(city.Person(name="Peter"))
            self.assertRaises(RuntimeError, session.run)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        sys.path.append("tests")
        server = TransportSessionServer(SimDummySession, HOST, PORT)
        print("ready", flush=True)
        server.startListening()
    else:
        unittest.main()
