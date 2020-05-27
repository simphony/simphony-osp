# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

# pip install pympler
import gc
import os
import time
import unittest2 as unittest
from osp.wrappers.sqlite import SqliteSession
from osp.core.utils.simple_search import find_cuds_object

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")

RUN_PERFORMANCE_TEST = False
DB = "performance_test.db"


class TestPerformance(unittest.TestCase):

    def setUp(self):
        if not RUN_PERFORMANCE_TEST:
            return
        self.iterations = 1000
        with SqliteSession(DB) as session:
            w = CITY.CITY_WRAPPER(session=session)
            self.fill_db(w, random_uid=False)
            session.commit()
        self.session = SqliteSession(DB)
        self.w = CITY.CITY_WRAPPER(session=self.session)
        gc.collect()
        self.start = time.time()

    def tearDown(self):
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
        for i in range(self.iterations):
            j = i * 9
            uids = iter([None for i in range(9)])
            if not random_uid:
                uids = iter(range(j * 9 + 1, (j + 1) * 9 + 1))
            c.add(CITY.CITIZEN(uid=next(uids)), rel=CITY.HAS_INHABITANT)
            c.add(CITY.CITIZEN(uid=next(uids)), rel=CITY.ENCLOSES)
            c.add(CITY.CITIZEN(uid=next(uids)), rel=CITY.HAS_PART)
            c.add(CITY.NEIGHBOURHOOD(name="", uid=next(uids)),
                  rel=CITY.HAS_INHABITANT)
            c.add(CITY.NEIGHBOURHOOD(name="", uid=next(uids)),
                  rel=CITY.ENCLOSES)
            c.add(CITY.NEIGHBOURHOOD(name="", uid=next(uids)),
                  rel=CITY.HAS_PART)
            c.add(CITY.STREET(name="", uid=next(uids)),
                  rel=CITY.HAS_INHABITANT)
            c.add(CITY.STREET(name="", uid=next(uids)), rel=CITY.ENCLOSES)
            c = c.add(CITY.STREET(name="", uid=next(uids)), rel=CITY.HAS_PART)

    def test_fill_db_one_commit(self):
        """
        Tests filling the db with lots of data with one commit
        """
        if not RUN_PERFORMANCE_TEST:
            return
        print("Test filling database one commit")
        self.fill_db(self.w)

    def test_graph_walk(self):
        """
        Traverse the graph
        """
        if not RUN_PERFORMANCE_TEST:
            return
        print("Traverse db")
        for i in range(self.iterations):
            find_cuds_object(lambda x: True, self.w, rel=CITY.ENCLOSES,
                             find_all=True, max_depth=10)
            self.session.commit()


if __name__ == '__main__':
    RUN_PERFORMANCE_TEST = True
    unittest.main()
