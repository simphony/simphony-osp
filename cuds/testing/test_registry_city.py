# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import cuds.classes
from cuds.classes.core.session.session import Session
from cuds.classes import ActiveRelationship


class TestRegistryCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_subtree(self):
        """
        Tests the get_subtree method.
        """
        c = cuds.classes.City("a city")
        p = cuds.classes.Citizen()
        n = cuds.classes.Neighbourhood("a neighborhood")
        s = cuds.classes.Street("The street")
        c.add(p, rel=cuds.classes.IsInhabitedBy)
        c.add(n)
        n.add(s)
        registry = c.session._registry
        self.assertEqual(
            registry.get_subtree(c.uid),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(c.uid, rel=ActiveRelationship),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(n.uid),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(n.uid, rel=ActiveRelationship),
            set([n, s]))

    def test_prune(self):
        """Tests the pruning method"""
        cities = list()
        for i in range(3):
            c = cuds.classes.City("city %s" % i)
            cities.append(c)
            for j in range(2):
                n = cuds.classes.Neighbourhood("neighborhood %s %s" % (i, j))
                c.add(n)
                for k in range(2):
                    s = cuds.classes.Street("street %s %s %s" % (i, j, k))
                    n.add(s)
        registry = cities[0].session._registry
        registry.prune(*[c.uid for c in cities[0:2]])
        self.assertEqual(
            set([k.name for k in registry.values()]),
            set(["city 0", "city 1", "neighborhood 0 0", "neighborhood 0 1",
                 "neighborhood 1 0", "neighborhood 1 1", "street 0 0 0",
                 "street 0 0 1", "street 0 1 0", "street 0 1 1",
                 "street 1 0 0", "street 1 0 1", "street 1 1 0",
                 "street 1 1 1"]))

        root, = [n for n in cities[0].get() if n.name == "neighborhood 0 0"]
        registry.prune(root, rel=ActiveRelationship)
        self.assertEqual(
            set([k.name for k in registry.values()]),
            set(["neighborhood 0 0",
                 "street 0 0 0",
                 "street 0 0 1"]))


if __name__ == '__main__':
    unittest.main()
