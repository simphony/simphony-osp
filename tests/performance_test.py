# pip install pympler
import gc
from pympler import asizeof
import time
import uuid
import unittest2 as unittest

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

RUN_PERFORMANCE_TEST = False


class TestPerformance(unittest.TestCase):

    def setUp(self):
        if not RUN_PERFORMANCE_TEST:
            return
        self.iterations = 100000
        self.c = city.City(name="A big city")
        for i in range(10):
            j = i * 9
            self.c.add(city.Citizen(uid=j + 0), rel=city.hasInhabitant)
            self.c.add(city.Citizen(uid=j + 1), rel=city.encloses)
            self.c.add(city.Citizen(uid=j + 2), rel=city.hasPart)
            self.c.add(city.Neighborhood(name="", uid=j + 3),
                       rel=city.hasInhabitant)
            self.c.add(city.Neighborhood(name="", uid=j + 4),
                       rel=city.encloses)
            self.c.add(city.Neighborhood(name="", uid=j + 5),
                       rel=city.hasPart)
            self.c.add(city.Street(name="", uid=j + 6),
                       rel=city.hasInhabitant)
            self.c.add(city.Street(name="", uid=j + 7), rel=city.encloses)
            self.c.add(city.Street(name="", uid=j + 8), rel=city.hasPart)
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
        """Tests the instantiation and type of the objects."""
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test cuds object creation")
        for i in range(self.iterations):
            city.Citizen(name='citizen ' + str(i))

    def test_add_default(self):
        """Tests the instantiation and type of the objects."""
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test adding with the default relationship")
        for i in range(self.iterations):
            self.c.add(city.Neighborhood(
                name='neighborhood ' + str(i)))

    def test_add_rel(self):
        """Tests the instantiation and type of the objects."""
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test adding with a general relationship")
        for i in range(self.iterations):
            self.c.add(city.Citizen(name='citizen ' + str(i)),
                       rel=city.hasInhabitant)

    def test_get_by_oclass(self):
        """Tests performance of getting by oclass."""
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test get by oclass")
        for i in range(self.iterations):
            self.c.get(oclass=city.Street)

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
            self.c.get(rel=city.hasInhabitant)


if __name__ == '__main__':
    RUN_PERFORMANCE_TEST = True
    unittest.main()
