# pip install pympler
import gc
from pympler import asizeof
import time
import uuid
import unittest2 as unittest

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")

RUN_PERFORMANCE_TEST = False


class TestPerformance(unittest.TestCase):

    def setUp(self):
        if not RUN_PERFORMANCE_TEST:
            return
        self.iterations = 100000
        self.c = CITY.CITY(name="A big city")
        for i in range(10):
            j = i * 9
            self.c.add(CITY.CITIZEN(uid=j + 0), rel=CITY.HAS_INHABITANT)
            self.c.add(CITY.CITIZEN(uid=j + 1), rel=CITY.ENCLOSES)
            self.c.add(CITY.CITIZEN(uid=j + 2), rel=CITY.HAS_PART)
            self.c.add(CITY.NEIGHBOURHOOD(name="", uid=j + 3),
                       rel=CITY.HAS_INHABITANT)
            self.c.add(CITY.NEIGHBOURHOOD(name="", uid=j + 4),
                       rel=CITY.ENCLOSES)
            self.c.add(CITY.NEIGHBOURHOOD(name="", uid=j + 5),
                       rel=CITY.HAS_PART)
            self.c.add(CITY.STREET(name="", uid=j + 6),
                       rel=CITY.HAS_INHABITANT)
            self.c.add(CITY.STREET(name="", uid=j + 7), rel=CITY.ENCLOSES)
            self.c.add(CITY.STREET(name="", uid=j + 8), rel=CITY.HAS_PART)
        self.start = time.time()

    def tearDown(self):
        if not RUN_PERFORMANCE_TEST:
            return
        self.stop = time.time()
        mem_bytes = asizeof.asizeof(self.c)
        mem_mb = mem_bytes / (1024 * 1024.0)
        print('Memory usage: ' + str(mem_mb) + ' MegaBytes.')
        total = self.stop - self.start
        if total > 60:
            print('Total time: ' + str(total / 60) + ' minutes.')
        else:
            print('Total time: ' + str(total) + ' seconds.')
        self.c._session = None
        gc.collect()

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test cuds object creation")
        for i in range(self.iterations):
            CITY.CITIZEN(name='citizen ' + str(i))

    def test_add_default(self):
        """
        Tests the instantiation and type of the objects
        """
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test adding with the default relationship")
        for i in range(self.iterations):
            self.c.add(CITY.NEIGHBORHOOD(
                name='neighborhood ' + str(i)))

    def test_add_rel(self):
        """
        Tests the instantiation and type of the objects
        """
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test adding with a general relationship")
        for i in range(self.iterations):
            self.c.add(CITY.CITIZEN(name='citizen ' + str(i)),
                       rel=CITY.HAS_INHABITANT)

    def test_get_by_oclass(self):
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test get by oclass")
        for i in range(self.iterations):
            self.c.get(oclass=CITY.STREET)

    def test_get_by_uid(self):
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test get by uid")
        uids = list(map(lambda x: uuid.UUID(int=x), range(10)))
        for i in range(self.iterations):
            self.c.get(*uids)

    def test_get_by_rel(self):
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test get by relationship")
        for i in range(self.iterations):
            self.c.get(rel=CITY.HAS_INHABITANT)


if __name__ == '__main__':
    RUN_PERFORMANCE_TEST = True
    unittest.main()
