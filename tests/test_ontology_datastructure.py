import os
import unittest2 as unittest
import tempfile
import rdflib
from rdflib.compare import isomorphic
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace_registry import NamespaceRegistry
from osp.core.ontology.installation import OntologyInstallationManager
from osp.core.ontology import OntologyClass, OntologyRelationship, \
    OntologyAttribute

CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")
RDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.ttl")


class TestParser(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.namespace_registry = NamespaceRegistry()
        self.namespace_registry._load_cuba()
        self.installer = OntologyInstallationManager(
            namespace_registry=self.namespace_registry,
            path=self.tempdir.name
        )
        self.graph = self.namespace_registry._graph

    def tearDown(self):
        self.tempdir.cleanup()

    def test_namespace_registry_load_cuba(self):
        g = rdflib.Graph()
        g.parse(CUBA_FILE, format="ttl")
        self.assertTrue(isomorphic(g, self.graph))
        self.assertIn("cuba", self.namespace_registry._namespaces)
        self.assertEqual(self.namespace_registry._namespaces["cuba"],
                         rdflib.URIRef("http://www.osp-core.com/cuba#"))

    def test_namespace_registry_store(self):
        self.graph.parse(RDF_FILE, format="ttl")
        self.graph.bind("parser_test",
                        rdflib.URIRef("http://www.osp-core.com/parser_test#"))
        self.namespace_registry.update_namespaces()
        self.namespace_registry.store(self.tempdir.name)
        self.assertEqual(os.listdir(self.tempdir.name), ["graph.ttl",
                                                         "namespaces.txt"])
        g = rdflib.Graph()
        g.parse(os.path.join(self.tempdir.name, "graph.ttl"), format="ttl")
        g1 = rdflib.Graph()
        g1.parse(CUBA_FILE, format="ttl")
        g1.parse(RDF_FILE, format="ttl")
        self.assertTrue(isomorphic(g, g1))

        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn("parser_test\thttp://www.osp-core.com/parser_test#",
                          lines)

    def test_namespace_registry_load(self):
        self.graph.parse(RDF_FILE, format="ttl")
        self.graph.bind("parser_test",
                        rdflib.URIRef("http://www.osp-core.com/parser_test#"))
        self.namespace_registry.update_namespaces()
        self.namespace_registry.store(self.tempdir.name)

        nr = NamespaceRegistry()
        nr.load(self.tempdir.name)
        self.assertTrue(isomorphic(nr._graph, self.graph))
        self.assertIn("parser_test", nr)

    def test_namespace_registry_clear(self):
        self.namespace_registry.clear()
        self.assertIsNot(self.namespace_registry._graph, self.graph)
        self.assertTrue(isomorphic(self.namespace_registry._graph, self.graph))

    def test_namespace_registry_from_iri(self):
        c = self.namespace_registry.from_iri(rdflib_cuba.Class)
        self.assertIsInstance(c, OntologyClass)
        self.assertEquals(c.namespace.get_name(), "cuba")
        self.assertEquals(c.name, "Class")
        r = self.namespace_registry.from_iri(rdflib_cuba.relationship)
        self.assertIsInstance(r, OntologyRelationship)
        self.assertEquals(r.namespace.get_name(), "cuba")
        self.assertEquals(r.name, "relationship")
        a = self.namespace_registry.from_iri(rdflib_cuba.attribute)
        self.assertIsInstance(a, OntologyAttribute)
        self.assertEquals(a.namespace.get_name(), "cuba")
        self.assertEquals(a.name, "attribute")

    def test_namespace_registry_update_namespaces(self):
        self.graph.bind("a", rdflib.URIRef("aaa"))
        self.graph.bind("b", rdflib.URIRef("bbb"))
        self.graph.bind("c", rdflib.URIRef("ccc"))
        self.namespace_registry.update_namespaces()
        self.assertEqual(self.namespace_registry.a.get_name(), "a")
        self.assertEqual(self.namespace_registry.a.get_iri(),
                         rdflib.URIRef("aaa"))
        self.assertEqual(self.namespace_registry.b.get_name(), "b")
        self.assertEqual(self.namespace_registry.b.get_iri(),
                         rdflib.URIRef("bbb"))
        self.assertEqual(self.namespace_registry.c.get_name(), "c")
        self.assertEqual(self.namespace_registry.c.get_iri(),
                         rdflib.URIRef("ccc"))

    def test_namespace_registry_get(self):
        self.installer.install("city")
        self.assertIn("city", self.namespace_registry)
        self.assertEqual(self.namespace_registry._get("city").get_name(),
                         "city")
        self.assertEqual(self.namespace_registry.get("city").get_name(),
                         "city")
        self.assertEqual(self.namespace_registry["city"].get_name(),
                         "city")
        self.assertEqual(self.namespace_registry.city.get_name(),
                         "city")
        self.assertRaises(KeyError, self.namespace_registry._get, "invalid")
        self.assertEquals(self.namespace_registry.get("invalid"), None)
        self.assertRaises(KeyError, self.namespace_registry.__getitem__,
                          "invalid")
        self.assertRaises(AttributeError, getattr, self.namespace_registry,
                          "invalid")
        self.assertEqual([x.get_name() for x in self.namespace_registry], [
                         'xml', 'rdf', 'rdfs', 'xsd', 'cuba', 'owl', 'city'])


if __name__ == "__main__":
    unittest.main()
