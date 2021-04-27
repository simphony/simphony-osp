"""This file contains tests for the abstract simulation session."""

from osp.wrappers.simdummy import SimDummySession
import unittest2 as unittest
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    Parser().parse("city")
    from osp.core.namespaces import city


class TestSimWrapperCity(unittest.TestCase):
    """Test simulation sessions with the city ontology."""

    def test_dummy_sim_wrapper(self):
        """Create a dummy simulation syntactic layer + test."""
        with SimDummySession() as session:
            wrapper = city.CitySimWrapper(numSteps=1, session=session)
            c = city.City(name="Freiburg")
            p1 = city.Person(name="Hans", age=34)
            p2 = city.Person(name="Renate", age=54)
            cw, _, _ = wrapper.add(c, p1, p2)

            session.run()

            self.assertEqual(len(
                wrapper.get(oclass=city.Person,
                            rel=city.hasPart)), 1)
            self.assertEqual(len(
                cw.get(oclass=city.Citizen,
                       rel=city.hasInhabitant)), 1)
            self.assertEqual(wrapper.get(p2.uid).name, "Renate")
            self.assertEqual(wrapper.get(p2.uid).age, 55)
            self.assertEqual(cw.get(p1.uid).name, "Hans")
            self.assertEqual(cw.get(p1.uid).age, 35)

            session.run()
            wrapper.add(city.Person(name="Peter"))
            self.assertRaises(RuntimeError, session.run)


if __name__ == '__main__':
    unittest.main()
