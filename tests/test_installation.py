"""Test the installation procedure."""

import os
import unittest2 as unittest
import tempfile
import rdflib
import shutil
from osp.core.ontology.installation import OntologyInstallationManager, \
    pico_migrate
from osp.core.ontology.namespace_registry import OntologySession

FILES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "parser_test.yml"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "osp", "core", "ontology", "files", "city.ontology.yml"),
]


class TestInstallation(unittest.TestCase):
    """Test the installation procedure."""

    def setUp(self):
        """Set up some temporary directories."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.namespace_registry = OntologySession()
        self.namespace_registry._load_cuba()
        self.installer = OntologyInstallationManager(
            namespace_registry=self.namespace_registry,
            path=self.tempdir.name
        )

    def tearDown(self):
        """Clean up temporary directories."""
        self.tempdir.cleanup()

    def copy_files(self):
        """Copy installed files.

        Helper method.
        """
        p1 = os.path.join(self.tempdir.name, os.path.basename(FILES[0]))
        p2 = os.path.join(self.tempdir.name, os.path.basename(FILES[1]))
        shutil.copyfile(FILES[0], p1)
        shutil.copyfile(FILES[1], p2)
        return p1, p2

    def test_do_install(self):
        """Test performing the installation."""
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
        self.assertEqual(sorted(os.listdir(self.tempdir.name)), sorted([
            'city.yml', 'graph.xml', 'namespaces.txt', 'parser_test.xml',
            'parser_test.yml']))
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
        self.assertEqual(sorted(os.listdir(self.tempdir.name)), sorted([
            'graph.xml', 'namespaces.txt', 'parser_test.xml',
            'parser_test.yml']))
        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertNotIn("city\thttp://www.osp-core.com/city#", lines)
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn("parser_test\thttp://www.osp-core.com/parser_test#",
                          lines)

    def test_conflicting_labels(self):
        """Tests that ontologies with conflicting labels fail to be installed.

        An example of such an ontology is the FOAF ontology, which has the same
        label for multiple IRIs. An error is only raised on installation if the
        reference_by_label option is set to Tue in the yml file.
        """
        FOAF = """
        identifier: foaf_TEST
        ontology_file: http://xmlns.com/foaf/spec/index.rdf
        reference_by_label: True
        namespaces:
            foaf_TEST: "http://xmlns.com/foaf/0.1/"
        active_relationships: []
        """

        foaf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        foaf_file.close()
        with open(foaf_file.name, 'w') as file:
            file.write(FOAF)
        self.assertRaises(KeyError, self.installer._install,
                          [foaf_file.name], lambda files: [foaf_file.name],
                          clear=False)
        os.remove(foaf_file.name)

    def test_get_new_packages(self):
        """Test getting new packages that need to be installed."""
        o1, o2 = self.copy_files()
        self.assertEqual(self.installer._get_new_packages(FILES), set())
        os.remove(o1)
        self.assertEqual(self.installer._get_new_packages(FILES), {FILES[0]})

    def test_get_replaced_packages(self):
        """Test packages to install after installation with overwrite."""
        o1, o2 = self.copy_files()
        self.assertEqual(
            set(self.installer._get_replaced_packages([FILES[0]])),
            {FILES[0], o2}
        )
        self.assertRaises(FileNotFoundError,
                          self.installer._get_replaced_packages, ["invalid"])

    def test_get_remaining_packages(self):
        """Test getting the remaining packages after un-installation."""
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
        """Test getting the packages currently installed."""
        o1, o2 = self.copy_files()
        open(os.path.join(self.tempdir.name, "o3.xml"), "w").close()
        self.assertEqual(self.installer.get_installed_packages(),
                         {"city", "parser_test"})
        self.assertEqual(self.installer.get_installed_packages(True),
                         {("city", o2), ("parser_test", o1)})

    def test_sort_for_installation(self):
        """Test sorting the packages to install by requirements."""
        r = self.installer._sort_for_installation(
            ["city", "parser_test"], set())
        self.assertEqual(r, ["city", "parser_test"])
        r = self.installer._sort_for_installation(
            ["parser_test", "city"], set())
        self.assertEqual(r, ["city", "parser_test"])
        self.assertRaises(RuntimeError, self.installer._sort_for_installation,
                          ["parser_test"], set())

    def test_pico_migrate(self):
        """Test migration of installed ontologies."""
        path = os.path.join(self.tempdir.name, ".osp_ontologies")
        yml_dir = os.path.join(path, "yml", "installed")
        os.makedirs(os.path.join(path, "yml", "installed"))
        file = FILES[1]
        dest = os.path.join(yml_dir, os.path.basename(file))
        shutil.copyfile(file, dest)
        pkl_file = os.path.join(path, "foo.bar.pkl")
        open(pkl_file, "wb").close()
        pico_migrate(self.installer.namespace_registry,
                     path)
        self.assertEqual(sorted(os.listdir(path)), sorted([
            'city.yml', 'graph.xml', 'namespaces.txt']))


if __name__ == "__main__":
    unittest.main()
