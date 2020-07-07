import os
import unittest2 as unittest
import tempfile
import rdflib
from rdflib.compare import isomorphic
from osp.core.ontology.namespace_registry import NamespaceRegistry
from osp.core.ontology.installation import OntologyInstallationManager

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
        pass

    def test_namespace_registry_clear(self):
        pass

    def test_namespace_registry_from_iri(self):
        pass

    def test_namespace_registry_update_namespaces(self):
        pass

    def test_namespace_registry_get(self):
        pass  # TODO iter, contains


if __name__ == "__main__":
    unittest.main()
