from osp.wrappers.simdummy import SimDummySession
import unittest2 as unittest
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")


class TestSimWrapperCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_dummy_sim_wrapper(self):
        """Create a dummy simulation syntactic layer + test
        if working with this layer works as expected.
        """
        with SimDummySession() as session:
            wrapper = CITY.CITY_SIM_WRAPPER(num_steps=1, session=session)
            c = CITY.CITY(name="Freiburg")
            p1 = CITY.PERSON(name="Hans", age=34)
            p2 = CITY.PERSON(name="Renate", age=54)
            cw, _, _ = wrapper.add(c, p1, p2)

            session.run()

            self.assertEqual(len(
                wrapper.get(oclass=CITY.PERSON,
                            rel=CITY.HAS_PART)), 1)
            self.assertEqual(len(
                cw.get(oclass=CITY.CITIZEN,
                       rel=CITY.HAS_INHABITANT)), 1)
            self.assertEqual(wrapper.get(p2.uid).name, "Renate")
            self.assertEqual(wrapper.get(p2.uid).age, 55)
            self.assertEqual(cw.get(p1.uid).name, "Hans")
            self.assertEqual(cw.get(p1.uid).age, 35)

            session.run()
            wrapper.add(CITY.PERSON(name="Peter"))
            self.assertRaises(RuntimeError, session.run)


if __name__ == '__main__':
    unittest.main()
