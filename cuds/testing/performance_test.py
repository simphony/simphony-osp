# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

# pip install pympler
from pympler import asizeof
import time
import unittest2 as unittest
import cuds.classes

RUN_PERFORMANCE_TEST = False


class TestPerformance(unittest.TestCase):

    def setUp(self):
        if not RUN_PERFORMANCE_TEST:
            return
        self.iterations = 500000
        self.c = cuds.classes.City("A big city")
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

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        if not RUN_PERFORMANCE_TEST:
            return
        for i in range(self.iterations):
            cuds.classes.Citizen(name='citizen ' + str(i))

    def test_add_default(self):
        """
        Tests the instantiation and type of the objects
        """
        if not RUN_PERFORMANCE_TEST:
            return
        for i in range(self.iterations):
            self.c.add(cuds.classes.Neighbourhood(
                'neighbourhood ' + str(i)))

    def test_add_rel(self):
        """
        Tests the instantiation and type of the objects
        """
        if not RUN_PERFORMANCE_TEST:
            return
        for i in range(self.iterations):
            self.c.add(cuds.classes.Citizen(name='citizen ' + str(i)),
                       rel=cuds.classes.HasInhabitant)


if __name__ == '__main__':
    RUN_PERFORMANCE_TEST = True
    unittest.main()
