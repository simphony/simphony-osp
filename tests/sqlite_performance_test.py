"""Test the performance of the SQLite Wrapper."""

# pip install pympler
import gc
import os
import time
import unittest2 as unittest
from osp.wrappers.sqlite import SqliteSession
from osp.core.utils.simple_search import find_cuds_object

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

RUN_PERFORMANCE_TEST = False
DB = "performance_test.db"


class TestPerformance(unittest.TestCase):
    """Test the performance of the SQLite Wrapper."""

    def setUp(self):
        """Start the timer and fill the database."""
        if not RUN_PERFORMANCE_TEST:
            return
        self.iterations = 1000
        with SqliteSession(DB) as session:
            w = city.CityWrapper(session=session)
            self.fill_db(w, random_uid=False)
            session.commit()
        self.session = SqliteSession(DB)
        self.w = city.CityWrapper(session=self.session)
        gc.collect()
        self.start = time.time()

    def tearDown(self):
        """Remove database file and print the performance of the test."""
        if not RUN_PERFORMANCE_TEST:
            return
        self.stop = time.time()
        total = self.stop - self.start
        if total > 60:
            print('Total time: ' + str(total / 60) + ' minutes.')
        else:
            print('Total time: ' + str(total) + ' seconds.')
        self.session.close()
        self.w._session = None
        gc.collect()
        if os.path.exists(DB):
            os.remove(DB)

    def fill_db(self, c, random_uid=True):
        """Fill the database with data."""
        for i in range(self.iterations):
            j = i * 9
            uids = iter([None for i in range(9)])
            if not random_uid:
                uids = iter(range(j * 9 + 1, (j + 1) * 9 + 1))
            c.add(city.Citizen(uid=next(uids)), rel=city.hasInhabitant)
            c.add(city.Citizen(uid=next(uids)), rel=city.encloses)
            c.add(city.Citizen(uid=next(uids)), rel=city.hasPart)
            c.add(city.Neighborhood(name="", uid=next(uids)),
                  rel=city.hasInhabitant)
            c.add(city.Neighborhood(name="", uid=next(uids)),
                  rel=city.encloses)
            c.add(city.Neighborhood(name="", uid=next(uids)),
                  rel=city.hasPart)
            c.add(city.Street(name="", uid=next(uids)),
                  rel=city.hasInhabitant)
            c.add(city.Street(name="", uid=next(uids)), rel=city.encloses)
            c = c.add(city.Street(name="", uid=next(uids)), rel=city.hasPart)

    def test_fill_db_one_commit(self):
        """Tests filling the db with lots of data with one commit."""
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test filling database one commit")
        self.fill_db(self.w)

    def test_graph_walk(self):
        """Traverse the graph."""
        if not RUN_PERFORMANCE_TEST:
            return
        print("Traverse db")
        for i in range(self.iterations):
            find_cuds_object(lambda x: True, self.w, rel=city.encloses,
                             find_all=True, max_depth=10)
            self.session.commit()


if __name__ == '__main__':
    RUN_PERFORMANCE_TEST = True
    unittest.main()
