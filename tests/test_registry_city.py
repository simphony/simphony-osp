# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
from osp.core import CUBA
from osp.core.cuds import Cuds
from .test_utils import get_test_city

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")


class TestRegistryCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_subtree(self):
        """
        Tests the get_subtree method.
        """
        c = CITY.CITY(name="a city")
        p = CITY.CITIZEN()
        n = CITY.NEIGHBOURHOOD(name="a neighbourhood")
        s = CITY.STREET(name="The street")
        c.add(p, rel=CITY.HAS_INHABITANT)
        c.add(n)
        n.add(s)
        registry = c.session._registry
        self.assertEqual(
            registry.get_subtree(c.uid),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(c.uid, rel=CUBA.ACTIVE_RELATIONSHIP),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(n.uid),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(n.uid, rel=CUBA.ACTIVE_RELATIONSHIP),
            set([n, s]))

    def test_prune(self):
        """Tests the pruning method"""
        cities = list()
        for i in range(3):
            c = CITY.CITY(name="city %s" % i)
            cities.append(c)
            for j in range(2):
                n = CITY.NEIGHBOURHOOD(name="neighbourhood %s %s" % (i, j))
                c.add(n)
                for k in range(2):
                    s = CITY.STREET(name="street %s %s %s" % (i, j, k))
                    n.add(s)
        registry = cities[0].session._registry
        registry.prune(*[c.uid for c in cities[0:2]])
        self.assertEqual(
            set([k.name for k in registry.values()]),
            set(["city 0", "city 1", "neighbourhood 0 0", "neighbourhood 0 1",
                 "neighbourhood 1 0", "neighbourhood 1 1", "street 0 0 0",
                 "street 0 0 1", "street 0 1 0", "street 0 1 1",
                 "street 1 0 0", "street 1 0 1", "street 1 1 0",
                 "street 1 1 1"]))

        root, = [n for n in cities[0].get() if n.name == "neighbourhood 0 0"]
        registry.prune(root, rel=CUBA.ACTIVE_RELATIONSHIP)
        self.assertEqual(
            set([k.name for k in registry.values()]),
            set(["neighbourhood 0 0",
                 "street 0 0 0",
                 "street 0 0 1"]))

    def test_filter(self):
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        found = registry.filter(lambda x: hasattr(x, "name")
                                and x.name == "Freiburg")
        self.assertEqual(found, {c.uid: c})
        found = registry.filter(lambda x: x.uid == n1.uid)
        self.assertEqual(found, {n1.uid: n1})
        found = registry.filter(lambda x: CITY.IS_PART_OF in x._neighbours)
        self.assertEqual(found, {n1.uid: n1,
                                 n2.uid: n2,
                                 s1.uid: s1})

    def test_filter_by_oclass(self):
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(
            registry.filter_by_oclass(CITY.CITY),
            {c.uid: c}
        )
        self.assertEqual(
            registry.filter_by_oclass(CITY.CITIZEN),
            {p1.uid: p1, p2.uid: p2, p3.uid: p3}
        )
        self.assertEqual(
            registry.filter_by_oclass(CITY.NEIGHBOURHOOD),
            {n1.uid: n1, n2.uid: n2}
        )

    def test_filter_by_attribute(self):
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(
            registry.filter_by_attribute("name", "Freiburg"),
            {c.uid: c}
        )
        self.assertEqual(
            registry.filter_by_attribute("age", 25),
            {p1.uid: p1, p2.uid: p2, p3.uid: p3}
        )

    def test_filter_by_relationship(self):
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.maxDiff = 2000
        self.assertEqual(
            registry.filter_by_relationships(
                CITY.IS_INHABITANT_OF
            ),
            {p1.uid: p1, p2.uid: p2, p3.uid: p3}
        )
        self.assertEqual(
            registry.filter_by_relationships(
                CITY.IS_PART_OF,
                consider_subrelationships=True
            ),
            {p3.uid: p3,
             n1.uid: n1, n2.uid: n2, s1.uid: s1}
        )


if __name__ == '__main__':
    unittest.main()
