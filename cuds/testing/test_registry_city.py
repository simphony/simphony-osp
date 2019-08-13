# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import cuds.classes
from cuds.classes import ActiveRelationship


class TestRegistryCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_subtree(self):
        """
        Tests the instantiation and type of the objects
        """
        c = cuds.classes.City("a city")
        p = cuds.classes.Citizen()
        n = cuds.classes.Neighbourhood("a neighborhood")
        s = cuds.classes.Street("The street")
        c.add(p, n)
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


if __name__ == '__main__':
    unittest.main()
