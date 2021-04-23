"""This file contains test for the registry using the city ontology."""

import unittest2 as unittest
from osp.core.namespaces import cuba
from osp.core.cuds import Cuds

try:
    from .test_utils import get_test_city
except ImportError:
    from test_utils import get_test_city


try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser(namespace_registry._graph).parse("city")
    namespace_registry.update_namespaces()
    city = namespace_registry.city


class TestRegistryCity(unittest.TestCase):
    """Tests for the registry."""

    def setUp(self):
        """Reset the core session."""
        from osp.core.cuds import Cuds
        from osp.core.session import CoreSession
        Cuds._session = CoreSession()

    def test_get_subtree(self):
        """Tests the get_subtree method."""
        c = city.City(name="a city")
        p = city.Citizen()
        n = city.Neighborhood(name="a neighborhood")
        s = city.Street(name="The street")
        c.add(p, rel=city.hasInhabitant)
        c.add(n)
        n.add(s)
        registry = c.session._registry
        self.assertEqual(
            registry.get_subtree(c.uid),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(c.uid, rel=cuba.activeRelationship),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(n.uid),
            set([c, p, n, s]))
        self.assertEqual(
            registry.get_subtree(n.uid, rel=cuba.activeRelationship),
            set([n, s]))

    def test_prune(self):
        """Test the pruning method."""
        cities = list()
        for i in range(3):
            c = city.City(name="city %s" % i)
            cities.append(c)
            for j in range(2):
                n = city.Neighborhood(name="neighborhood %s %s" % (i, j))
                c.add(n)
                for k in range(2):
                    s = city.Street(name="street %s %s %s" % (i, j, k))
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
        registry.prune(root, rel=cuba.activeRelationship)
        self.assertEqual(
            set([k.name for k in registry.values()]),
            set(["neighborhood 0 0",
                 "street 0 0 0",
                 "street 0 0 1"]))

    def test_get_not_reachable(self):
        """Test the pruning method."""
        cities = list()
        for i in range(3):
            c = city.City(name="city %s" % i)
            cities.append(c)
            for j in range(2):
                n = city.Neighborhood(name="neighborhood %s %s" % (i, j))
                c.add(n)
                for k in range(2):
                    s = city.Street(name="street %s %s %s" % (i, j, k))
                    n.add(s)
        registry = cities[0].session._registry
        result = registry._get_not_reachable(cities[2].uid)
        self.assertEqual(
            set([k.name for k in result]),
            set(["city 0", "city 1", "neighborhood 0 0", "neighborhood 0 1",
                 "neighborhood 1 0", "neighborhood 1 1", "street 0 0 0",
                 "street 0 0 1", "street 0 1 0", "street 0 1 1",
                 "street 1 0 0", "street 1 0 1", "street 1 1 0",
                 "street 1 1 1"]))

        roots = [
            n for n in cities[0].get() if n.name.startswith("neighborhood 0")
        ]
        registry.prune(*roots, rel=cuba.passiveRelationship)
        self.assertEqual(
            set([k.name for k in registry.values()]),
            set(["neighborhood 0 0", "neighborhood 0 1", "city 0"]))

    def test_filter(self):
        """Test the filter method."""
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        found = registry.filter(lambda x: hasattr(x, "name")
                                and x.name == "Freiburg")
        self.assertEqual(found, {c.uid: c})
        found = registry.filter(lambda x: x.uid == n1.uid)
        self.assertEqual(found, {n1.uid: n1})
        found = registry.filter(lambda x: city.isPartOf in x._neighbors)
        self.assertEqual(found, {n1.uid: n1,
                                 n2.uid: n2,
                                 s1.uid: s1})

    def test_filter_by_oclass(self):
        """Test filtering by ontology class."""
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(
            registry.filter_by_oclass(city.City),
            {c.uid: c}
        )
        self.assertEqual(
            registry.filter_by_oclass(city.Citizen),
            {p1.uid: p1, p2.uid: p2, p3.uid: p3}
        )
        self.assertEqual(
            registry.filter_by_oclass(city.Neighborhood),
            {n1.uid: n1, n2.uid: n2}
        )

    def test_filter_by_attribute(self):
        """Test filter_by_attribute method."""
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
        """Test filter_by_relationships."""
        registry = Cuds._session._registry
        registry.reset()
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.maxDiff = 2000
        self.assertEqual(
            registry.filter_by_relationships(
                city.INVERSE_OF_hasInhabitant
            ),
            {p1.uid: p1, p2.uid: p2, p3.uid: p3}
        )
        self.assertEqual(
            registry.filter_by_relationships(
                city.isPartOf,
                consider_subrelationships=True
            ),
            {p3.uid: p3,
             n1.uid: n1, n2.uid: n2, s1.uid: s1}
        )


if __name__ == '__main__':
    unittest.main()
