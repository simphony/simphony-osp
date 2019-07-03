# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import time
import cuds.classes


class TestPerformance(unittest.TestCase):

    def setUp(self):
        self.iterations = 500000
        self.c = cuds.classes.City("A big city")
        self.start = time.time()

    def tearDown(self):
        self.stop = time.time()
        total = self.stop - self.start
        if total > 60:
            print('Total time: ' + str(total / 60) + ' minutes.')
        else:
            print('Total time: ' + str(total) + ' seconds.')

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        for i in range(self.iterations):
            cuds.classes.Citizen('citizen ' + str(i))

    def test_add_default(self):
        """
        Tests the instantiation and type of the objects
        """
        for i in range(self.iterations):
            self.c.add(cuds.classes.Citizen('citizen ' + str(i)))

    def test_add_rel(self):
        """
        Tests the instantiation and type of the objects
        """
        for i in range(self.iterations):
            self.c.add(cuds.classes.Citizen('citizen ' + str(i)),
                       rel=cuds.classes.Encloses)


if __name__ == '__main__':
    unittest.main()
