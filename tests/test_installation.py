import os
import unittest2 as unittest
import tempfile
import rdflib
import shutil
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

    def copy_files(self):
        p1 = os.path.join(self.tempdir.name, os.path.basename(FILES[0]))
        p2 = os.path.join(self.tempdir.name, os.path.basename(FILES[1]))
        shutil.copyfile(FILES[0], p1)
        shutil.copyfile(FILES[1], p2)
        return p1, p2

    def test_do_install(self):
        # clear False
        self.installer._install(FILES + ["invalid"], lambda x: x[:-1],
                                clear=False)
        self.assertIn("city", self.namespace_registry._namespaces)
        self.assertIn("parser_test", self.namespace_registry._namespaces)
        self.assertEqual(self.namespace_registry._namespaces["city"],
                         rdflib.term.URIRef('http://www.osp-core.com/city#'))
        self.assertEqual(
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
        self.assertEqual(
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
        o1, o2 = self.copy_files()
        self.assertEqual(self.installer._get_new_packages(FILES), set())
        os.remove(o1)
        self.assertEqual(self.installer._get_new_packages(FILES), {FILES[0]})

    def test_get_replaced_packages(self):
        o1, o2 = self.copy_files()
        self.assertEqual(
            set(self.installer._get_replaced_packages([FILES[0]])),
            {FILES[0], o2}
        )
        self.assertRaises(FileNotFoundError,
                          self.installer._get_replaced_packages, ["invalid"])

    def test_get_remaining_packages(self):
        o1, o2 = self.copy_files()
        self.assertRaises(
            ValueError, self.installer._get_remaining_packages,
            ["city", "invalid"]
        )
        self.assertRaises(
            ValueError, self.installer._get_remaining_packages, ["city.yml"]
        )
        self.assertEqual(self.installer._get_remaining_packages(FILES), [])
        self.assertEqual(self.installer._get_remaining_packages([FILES[0]]),
                         [o2])
        self.assertEqual(self.installer._get_remaining_packages([o2]),
                         [o1])
        os.remove(o2)
        self.assertRaises(ValueError, self.installer._get_remaining_packages,
                          FILES)

    def test_get_installed_packages(self):
        o1, o2 = self.copy_files()
        open(os.path.join(self.tempdir.name, "o3.ttl"), "w").close()
        self.assertEqual(self.installer.get_installed_packages(),
                         ["city", "parser_test"])
        self.assertEqual(self.installer.get_installed_packages(True),
                         [("city", o2), ("parser_test", o1)])


if __name__ == "__main__":
    unittest.main()
