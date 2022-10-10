"""Test the installation procedure."""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable, Tuple, Type, Union

import unittest2 as unittest
from rdflib import URIRef

import osp.core.warnings as warning_settings
from osp.core.ontology.installation import (
    OntologyInstallationManager,
    pico_migrate,
)
from osp.core.ontology.namespace_registry import (
    NamespaceRegistry,
    namespace_registry,
)
from osp.core.ontology.parser.owl.parser import RDFPropertiesWarning, logger
from osp.core.ontology.parser.parser import Parser
from osp.core.pico import install, namespaces, packages, uninstall

FILES = [
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "parser_test.yml"
    ),
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "osp",
        "core",
        "ontology",
        "docs",
        "city.ontology.yml",
    ),
]

FILE_WITH_UNSATISFIABLE_REQUIREMENTS = f"""
identifier: parser_test
namespaces:
    parser_test: http://www.osp-core.com/parser_test
ontology_file: {os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "parser_test.ttl")}
format: "ttl"
default_relationship: http://www.osp-core.com/parser_test#relationshipA
active_relationships:
  - http://www.osp-core.com/parser_test#relationshipA
  - http://www.osp-core.com/parser_test#relationshipB
requirements:
  - fictional_package
"""


class TestInstallation(unittest.TestCase):
    """Test the installation procedure."""

    _rdf_file: tempfile.NamedTemporaryFile
    """RDF file that does NOT contain an ontology."""

    _yml_file: tempfile.NamedTemporaryFile
    """YML configuration file for the previous file."""

    @classmethod
    def setUpClass(cls):
        """Create additional ontology files."""
        cls._rdf_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".ttl", mode="w"
        )
        cls._rdf_file.write(
            "@prefix ns1: <none:> .\n" "ns1:a ns1:meaningless ns1:triple .\n\n"
        )
        cls._rdf_file.close()
        cls._yml_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".yml", mode="w"
        )
        cls._yml_file.write(
            f"identifier: test_pkg\n"
            f"ontology_file: {cls._rdf_file.name}\n"
            f"format: ttl\n"
            f"reference_by_label: False\n"
            f"namespaces: \n"
            f'    none: "none:"\n'
            f"active_relationships: []\n"
        )
        cls._yml_file.close()

    @classmethod
    def tearDownClass(cls):
        """Delete extra ontology files created during class setup."""
        Path(cls._rdf_file.name).unlink()
        Path(cls._yml_file.name).unlink()

    def setUp(self):
        """Set up some temporary directories."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.namespace_registry = NamespaceRegistry()
        self.namespace_registry._load_cuba()
        self.installer = OntologyInstallationManager(
            namespace_registry=self.namespace_registry, path=self.tempdir.name
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
        self.installer._install(
            FILES + ["invalid"], lambda x: x[:-1], clear=False
        )
        self.assertIn("city", self.namespace_registry._namespaces)
        self.assertIn("parser_test", self.namespace_registry._namespaces)
        self.assertEqual(
            self.namespace_registry._namespaces["city"],
            URIRef("http://www.osp-core.com/city#"),
        )
        self.assertEqual(
            self.namespace_registry._namespaces["parser_test"],
            URIRef("http://www.osp-core.com/parser_test#"),
        )
        self.assertEqual(
            sorted(os.listdir(self.tempdir.name)),
            sorted(
                [
                    "city.yml",
                    "graph.xml",
                    "namespaces.txt",
                    "parser_test.xml",
                    "parser_test.yml",
                ]
            ),
        )
        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertIn("city\thttp://www.osp-core.com/city#", lines)
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn(
                "parser_test\thttp://www.osp-core.com/parser_test#", lines
            )
        g_old = self.namespace_registry._graph

        # clear False
        self.installer._install([FILES[0]], lambda x: x, clear=True)
        self.assertNotIn("city", self.namespace_registry._namespaces)
        self.assertIn("parser_test", self.namespace_registry._namespaces)
        self.assertIsNot(g_old, self.namespace_registry._graph)
        self.assertEqual(
            self.namespace_registry._namespaces["parser_test"],
            URIRef("http://www.osp-core.com/parser_test#"),
        )
        self.assertEqual(
            sorted(os.listdir(self.tempdir.name)),
            sorted(
                [
                    "graph.xml",
                    "namespaces.txt",
                    "parser_test.xml",
                    "parser_test.yml",
                ]
            ),
        )
        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertNotIn("city\thttp://www.osp-core.com/city#", lines)
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn(
                "parser_test\thttp://www.osp-core.com/parser_test#", lines
            )

    def test_conflicting_labels(self):
        """Tests that ontologies with conflicting labels fail to be installed.

        An example of such an ontology is the FOAF ontology, which has the same
        label for multiple IRIs. An error is only raised on installation if the
        reference_by_label option is set to Tue in the yml file.
        """
        FOAF_URL = (
            "https://web.archive.org/web/20220614185720if_/"
            "http://xmlns.com/foaf/spec/index.rdf"
        )
        FOAF = f"""
        identifier: foaf_TEST
        ontology_file: "{FOAF_URL}"
        reference_by_label: True
        namespaces:
            foaf_TEST: "http://xmlns.com/foaf/0.1/"
        active_relationships: []
        """

        foaf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
        foaf_file.close()
        with open(foaf_file.name, "w") as file:
            file.write(FOAF)
        self.assertRaises(
            KeyError,
            self.installer._install,
            [foaf_file.name],
            lambda files: [foaf_file.name],
            clear=False,
        )
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
            {FILES[0], o2},
        )
        self.assertRaises(
            FileNotFoundError,
            self.installer._get_replaced_packages,
            ["invalid"],
        )

    def test_get_remaining_packages(self):
        """Test getting the remaining packages after un-installation."""
        o1, o2 = self.copy_files()
        self.assertRaises(
            ValueError,
            self.installer._get_remaining_packages,
            ["city", "invalid"],
        )
        self.assertRaises(
            ValueError, self.installer._get_remaining_packages, ["city.yml"]
        )
        self.assertEqual(self.installer._get_remaining_packages(FILES), [])
        self.assertEqual(
            self.installer._get_remaining_packages([FILES[0]]), [o2]
        )
        self.assertEqual(self.installer._get_remaining_packages([o2]), [o1])
        os.remove(o2)
        self.assertRaises(
            ValueError, self.installer._get_remaining_packages, FILES
        )

    def test_get_installed_packages(self):
        """Test getting the packages currently installed."""
        o1, o2 = self.copy_files()
        open(os.path.join(self.tempdir.name, "o3.xml"), "w").close()
        self.assertEqual(
            self.installer.get_installed_packages(), {"city", "parser_test"}
        )
        self.assertEqual(
            self.installer.get_installed_packages(True),
            {("city", o2), ("parser_test", o1)},
        )

    def test_sort_for_installation(self):
        """Test sorting the packages to install by requirements."""
        r = self.installer._sort_for_installation(
            ["city", "parser_test"], set()
        )
        self.assertEqual(r, ["city", "parser_test"])
        r = self.installer._sort_for_installation(
            ["parser_test", "city"], set()
        )
        self.assertEqual(r, ["city", "parser_test"])

        # Test unsatisfiable requirements
        with tempfile.TemporaryDirectory():
            with open("ontology_file.yml", "w") as file:
                file.write(FILE_WITH_UNSATISFIABLE_REQUIREMENTS)
            self.assertRaises(
                RuntimeError,
                self.installer._sort_for_installation,
                [file.name],
                set(),
            )

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
        pico_migrate(self.installer.namespace_registry, path)
        self.assertEqual(
            sorted(os.listdir(path)),
            sorted(["city.yml", "graph.xml", "namespaces.txt"]),
        )

    def test_empty_file(self):
        """Tests installing an RDF file NOT containing an ontology."""

        def install_empty_file():
            """Install an RDF file that contains no ontology information."""
            self.installer._install(
                [self._yml_file.name], lambda x: (x for x in x), clear=False
            )

        self.assertRaises(RuntimeError, install_empty_file)

    def test_dcterms(self):
        """Test DCMI Metadata Terms installation."""

        def count_warnings_by_class(
            records: Iterable[logging.LogRecord],
            classes: Union[Type, Tuple[Type, ...]],
        ) -> int:
            """Given log records, count their "classes" if attached.

            For each record, checks if it has a `warning_class` attribute,
            and checks whether its value is a subclass of the classes
            provided.
            """
            return sum(
                bool(
                    issubclass(record.warning_class, classes)
                    if hasattr(record, "warning_class")
                    else False
                )
                for record in records
            )

        original_warning_setting = warning_settings.rdf_properties_warning
        try:
            warning_settings.rdf_properties_warning = False
            with self.assertLogs(logger=logger) as captured:
                logger.warning(
                    "At least one log entry is needed for " "`assertLogs`."
                )
                self.installer._install(
                    ["dcterms", "dcmitype"],
                    lambda x: (x for x in x),
                    clear=True,
                )
                self.assertEqual(
                    count_warnings_by_class(
                        captured.records, (RDFPropertiesWarning,)
                    ),
                    0,
                )

            warning_settings.rdf_properties_warning = True
            with self.assertLogs(logger=logger) as captured:
                logger.warning(
                    "At least one log entry is needed for " "`assertLogs`."
                )
                self.installer._install(
                    ["dcterms", "dcmitype"],
                    lambda x: (x for x in x),
                    clear=True,
                )
                self.assertEqual(
                    count_warnings_by_class(
                        captured.records, (RDFPropertiesWarning,)
                    ),
                    1,  # dcmi-type has no properties
                )
        finally:
            warning_settings.rdf_properties_warning = original_warning_setting


class PicoModule(unittest.TestCase):
    """Test the use of pico as a Python module."""

    def setUp(self) -> None:
        """Change installation path and reset the namespace registry."""
        self._previous_installation_path = (
            OntologyInstallationManager.get_default_installation_path()
        )
        self._new_installation_path = Path(
            ".TEST_OSP_CORE_INSTALLATION"
        ).absolute()
        os.makedirs(
            self._new_installation_path / ".osp_ontologies", exist_ok=True
        )
        OntologyInstallationManager.set_default_installation_path(
            str(self._new_installation_path)
        )
        namespace_registry.clear()
        namespace_registry.load_graph_file(
            OntologyInstallationManager.get_default_installation_path()
        )

    def tearDown(self) -> None:
        """Revert changes done during the execution of the `setUp` method."""
        OntologyInstallationManager.set_default_installation_path(
            str(Path(self._previous_installation_path).parent)
        )
        shutil.rmtree(self._new_installation_path)
        namespace_registry.clear()
        namespace_registry.load_graph_file(
            OntologyInstallationManager.get_default_installation_path()
        )
        # Restore also ontologies loaded by the test runner.
        if Parser.load_history:
            parser = Parser()
            for path in Parser.load_history:
                parser.parse(path)

    def test_pico(self):
        """Tests operating pico as a Python module."""
        self.assertSetEqual(set(), set(packages()))

        install(*FILES)
        from osp.core.namespaces import city, cuba, parser_test

        self.assertSetEqual({"city", "parser_test"}, set(packages()))
        self.assertSetEqual({cuba, city, parser_test}, set(namespaces()))

        import osp.core.namespaces

        uninstall("city")
        self.assertSetEqual({"parser_test"}, set(packages()))
        self.assertRaises(AttributeError, lambda: city.City)
        self.assertRaises(
            AttributeError, lambda: getattr(osp.core.namespaces, "city")
        )

        install("city")
        self.assertSetEqual({"city", "parser_test"}, set(packages()))
        self.assertSetEqual({cuba, city, parser_test}, set(namespaces()))
        self.assertEqual(
            city.City.iri, URIRef("http://www.osp-core.com/city#City")
        )


if __name__ == "__main__":
    unittest.main()
