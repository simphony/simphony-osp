import os
import unittest2 as unittest
import tempfile
import rdflib
from osp.core.ontology.installation import OntologyInstallationManager
from osp.core.ontology.namespace_registry import NamespaceRegistry

FILES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "parser_test.yml"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "osp", "core", "ontology", "docs", "city.ontology.yml"),
]


class TestParser(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.namespace_registry = NamespaceRegistry()
        self.namespace_registry._load_cuba()
        self.installer = OntologyInstallationManager(
            namespace_registry=self.namespace_registry,
            path=self.tempdir.name
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_do_install(self):
        # clear False
        self.installer._install(FILES + ["invalid"], lambda x: x[:-1],
                                clear=False)
        self.assertIn("city", self.namespace_registry._namespaces)
        self.assertIn("parser_test", self.namespace_registry._namespaces)
        self.assertEquals(self.namespace_registry._namespaces["city"],
                          rdflib.term.URIRef('http://www.osp-core.com/city#'))
        self.assertEquals(
            self.namespace_registry._namespaces["parser_test"],
            rdflib.term.URIRef('http://www.osp-core.com/parser_test#'))
        self.assertEqual(os.listdir(self.tempdir.name), [
            'city.yml', 'graph.ttl', 'namespaces.txt', 'parser_test.ttl',
            'parser_test.yml'])
        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertIn("city\thttp://www.osp-core.com/city#", lines)
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn("parser_test\thttp://www.osp-core.com/parser_test#",
                          lines)
        g_old = self.namespace_registry._graph

        # clear False
        self.installer._install([FILES[0]], lambda x: x, clear=True)
        self.assertNotIn("city", self.namespace_registry._namespaces)
        self.assertIn("parser_test", self.namespace_registry._namespaces)
        self.assertIsNot(g_old, self.namespace_registry._graph)
        self.assertEquals(
            self.namespace_registry._namespaces["parser_test"],
            rdflib.term.URIRef('http://www.osp-core.com/parser_test#'))
        self.assertEqual(os.listdir(self.tempdir.name), [
            'graph.ttl', 'namespaces.txt', 'parser_test.ttl',
            'parser_test.yml'])
        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertNotIn("city\thttp://www.osp-core.com/city#", lines)
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn("parser_test\thttp://www.osp-core.com/parser_test#",
                          lines)

    def test_get_new_packages(self):
        pass

    def test_get_replaced_packages(self):
        pass

    def test_get_remaining_packages(self):
        pass

    def test_get_installed_packages(self):
        pass


if __name__ == "__main__":
    unittest.main()
