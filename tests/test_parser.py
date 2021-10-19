"""Test the default parser used for parsing OWL ontologies."""

import os
import re
import shutil
import tempfile
import yaml
from pathlib import Path

import responses
import rdflib
import unittest2 as unittest
from rdflib.compare import isomorphic

from osp.core.ontology.namespace_registry import NamespaceRegistry
from osp.core.ontology.parser import Parser
from osp.core.ontology.parser.parser import OntologyParser


RDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.ttl")
CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")
YML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.yml")
with open(YML_FILE) as f:
    YML_DOC = yaml.safe_load(f)


class TestParser(unittest.TestCase):
    """Test the default parser used for parsing OWL ontologies."""

    def setUp(self):
        """Set up Graph and Parser."""
        self.namespace_registry = NamespaceRegistry()
        self.graph = self.namespace_registry._graph
        self.parser = Parser(parser_namespace_registry=self.namespace_registry)
        with open(YML_FILE, 'r') as file:
            self.config_file = yaml.safe_load(file)

    def test_parse_rdf(self):
        """Test parsing an rdf file."""
        with tempfile.TemporaryDirectory() as tempdir:
            new_config = self.config_file
            new_config['namespaces'] = {}
            new_yml_path = os.path.join(tempdir,
                                        os.path.basename(YML_FILE))
            new_ttl_path = os.path.join(tempdir,
                                        os.path.basename(RDF_FILE))
            with open(new_yml_path, 'w') as file:
                yaml.dump(new_config, file)
            shutil.copy(RDF_FILE, new_ttl_path)
            self.assertRaises(TypeError, new_yml_path, self.parser.parse)
        with tempfile.TemporaryDirectory() as tempdir:
            new_config = self.config_file
            new_config['identifier'] = 'x'
            new_yml_path = os.path.join(tempdir,
                                        os.path.basename(YML_FILE))
            new_ttl_path = os.path.join(tempdir,
                                        os.path.basename(RDF_FILE))
            with open(new_yml_path, 'w') as file:
                yaml.dump(new_config, file)
            shutil.copy(RDF_FILE, new_ttl_path)
            self.assertRaises(TypeError, new_yml_path, self.parser.parse)
        with tempfile.TemporaryDirectory() as tempdir:
            new_config = self.config_file
            new_config['namespaces'] = {}
            new_config['identifier'] = 'x'
            new_config['invalid'] = True
            new_yml_path = os.path.join(tempdir,
                                        os.path.basename(YML_FILE))
            new_ttl_path = os.path.join(tempdir,
                                        os.path.basename(RDF_FILE))
            with open(new_yml_path, 'w') as file:
                yaml.dump(new_config, file)
            shutil.copy(RDF_FILE, new_ttl_path)
            self.assertRaises(TypeError, new_yml_path, self.parser.parse)
        with tempfile.TemporaryDirectory() as tempdir:
            config = dict(
                identifier="parser_test",
                ontology_file=RDF_FILE,
                namespaces={
                    "parser_test": "http://www.osp-core.com/parser_test"
                },
                format="ttl",
                file='file.ttl'
            )
            new_yml_path = os.path.join(tempdir, 'file.yml')
            new_ttl_path = os.path.join(tempdir, 'file.ttl')
            with open(new_yml_path, 'w') as file:
                yaml.dump(config, file)
            shutil.copy(RDF_FILE, new_ttl_path)
            rdf = rdflib.Graph()
            rdf.parse(RDF_FILE, format="ttl")
            parser = OntologyParser.get_parser(new_yml_path)
            graph = parser.graph
        self.assertEqual(len(graph), len(rdf))
        self.assertTrue(isomorphic(graph, rdf))
        self.assertIn(rdflib.URIRef("http://www.osp-core.com/parser_test#"),
                      list(parser.namespaces.values()))

    def test_parse_yml(self):
        """Test parsing the yaml file."""
        with tempfile.TemporaryDirectory() as tempdir:
            yml_path = os.path.join(tempdir, 'test.yml')
            with open(yml_path, 'w') as file:
                invalid = dict(YML_DOC)
                invalid["identifier"] = "parser.test"
                yaml.safe_dump(invalid, file)
            self.assertRaises(ValueError, OntologyParser.get_parser,
                              yml_path)

    @responses.activate
    def test_parse_yml_download(self):
        """Test downloading owl ontologies."""
        def request_callback(request):
            headers = {'request-id': '728d329e-0e86-11e4-a748-0c84dc037c13'}
            return 200, headers, "<ns1:a> <ns1:b> <ns1:c> ."

        url = "http://my_ontology.com/ontology.owl"
        responses.add_callback(
            responses.GET, url,
            callback=request_callback,
            content_type='text/plain',
        )
        doc = dict(YML_DOC)
        doc["ontology_file"] = url
        with tempfile.TemporaryDirectory() as tempdir:
            yml_path = os.path.join(tempdir, 'parser_test.yml')
            with open(yml_path, 'w') as file:
                yaml.safe_dump(doc, file)
            parser = OntologyParser.get_parser(yml_path)
            self.assertIn((rdflib.URIRef("ns1:a"), rdflib.URIRef("ns1:b"),
                           rdflib.URIRef("ns1:c")), parser.graph)

    def test_get_file_path(self):
        """Test the get_file_path method."""
        self.assertEqual(OntologyParser.parse_file_path("test/my_file.yml"),
                         "test/my_file.yml")
        self.assertEqual(
            OntologyParser.parse_file_path("my_file").lower(),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "my_file.yml"
            ))).lower()
        )
        self.assertEqual(
            OntologyParser.parse_file_path("emmo").lower(),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "emmo.yml"
            ))).lower()
        )
        self.assertEqual(
            OntologyParser.parse_file_path("city").lower(),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "city.ontology.yml"
            ))).lower()
        )

    def test_get_identifier(self):
        """Test the get_identifier method."""
        self.assertEqual(OntologyParser.get_parser(YML_FILE).identifier,
                         "parser_test")
        self.assertEqual(OntologyParser.get_parser("parser_test").identifier,
                         "parser_test")
        self.assertEqual(OntologyParser.get_parser("emmo").identifier, "emmo")

    def test_get_namespace_name(self):
        """Test the get_namespace_name method."""
        self.assertItemsEqual(OntologyParser
                              .get_parser(YML_FILE).namespaces.keys(),
                              ["parser_test"])
        self.assertItemsEqual(OntologyParser
                              .get_parser("parser_test").namespaces.keys(),
                              ["parser_test"])
        self.assertItemsEqual(OntologyParser
                              .get_parser("emmo").namespaces.keys(),
                              ['mereotopology', 'physical', 'top', 'semiotics',
                               'perceptual', 'reductionistic', 'holistic',
                               'physicalistic', 'math', 'properties',
                               'materials', 'metrology', 'models',
                               'manufacturing', 'isq', 'siunits'])

    def test_get_requirements(self):
        """Test the get_requirements() method."""
        self.assertEqual(OntologyParser.get_parser(YML_FILE).requirements,
                         set())
        self.assertEqual(OntologyParser.get_parser("parser_test").requirements,
                         {"city"})

    def test_install(self):
        """Test the store method."""
        parser = OntologyParser.get_parser(YML_FILE)
        with tempfile.TemporaryDirectory() as destination:
            parser.install(destination)
            self.assertItemsEqual(os.listdir(destination),
                                  ["parser_test.xml", "parser_test.yml"])
            with open(os.path.join(destination, "parser_test.yml")) as f:
                yml_doc = yaml.safe_load(f)
                self.assertEqual(yml_doc["ontology_file"], "parser_test.xml")
                yml_doc["ontology_file"] = YML_DOC["ontology_file"]
                self.assertEqual(yml_doc["format"], "xml")
                copy = YML_DOC.copy()
                del yml_doc["format"]
                del copy["format"]
                self.assertEqual(yml_doc, copy)
            g = rdflib.Graph()
            g.parse(os.path.join(destination, "parser_test.xml"),
                    format="xml")
            self.assertTrue(
                isomorphic(g, parser.graph))

    def test_parse(self):
        """Test the parsing a file."""
        parser = OntologyParser.get_parser(YML_FILE)
        g1 = rdflib.Graph()
        g1.parse(RDF_FILE, format="ttl")
        self.assertTrue(parser.graph, g1)

    def test_parse_guess_format(self):
        """Test the parsing a file without providing the format."""
        modified_yml_config_path = Path(YML_FILE)
        modified_yml_config_path = str(modified_yml_config_path.with_name(
            modified_yml_config_path.stem + '_mod'
            + modified_yml_config_path.suffix))
        try:
            # Create a copy of YML_FILE and remove the 'format' keyword.
            with open(modified_yml_config_path, 'w') as modified_yml_config:
                with open(YML_FILE, 'r') as yml_config:
                    modified_yml_config.write(
                        re.sub(r'^[\s]*format:[\s].*', '',
                               yml_config.read(), flags=re.MULTILINE))

            parser = OntologyParser.get_parser(modified_yml_config_path)
            g1 = rdflib.Graph()
            g1.parse(RDF_FILE, format="ttl")
            self.assertTrue(parser.graph, g1)
        finally:
            if os.path.exists(modified_yml_config_path):
                os.remove(modified_yml_config_path)


if __name__ == "__main__":
    unittest.main()
