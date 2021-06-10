"""Test the default parser used for parsing OWL ontologies."""

import os
import yaml
import rdflib
import unittest2 as unittest
import tempfile
import responses
from rdflib.compare import isomorphic
from osp.core.ontology.parser.owl_DELETE import Parser
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace_registry import NamespaceRegistry


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

    def test_add_cuba_triples(self):
        """Test adding the cuba triples, like active relationships."""
        self.graph.add((rdflib.URIRef("has_part"), rdflib.RDF.type,
                        rdflib.OWL.ObjectProperty))
        self.graph.add((rdflib.URIRef("encloses"), rdflib.RDF.type,
                        rdflib.OWL.ObjectProperty))
        pre = set(self.graph)
        self.parser._add_cuba_triples([
            rdflib.URIRef("has_part"), rdflib.URIRef("encloses")
        ])
        self.assertEqual(set(self.graph) - pre, {
            (rdflib.URIRef("encloses"), rdflib.RDFS.subPropertyOf,
             rdflib_cuba.activeRelationship),
            (rdflib.URIRef("has_part"), rdflib.RDFS.subPropertyOf,
             rdflib_cuba.activeRelationship)
        })

    def test_add_default_rel_triples(self):
        """Test adding the default rel triples."""
        self.parser._add_default_rel_triples({
            "ns1": "has_part",
            "ns2": "encloses"
        })
        self.assertEqual(set(self.graph), {
            (rdflib.URIRef("ns1"), rdflib_cuba._default_rel,
             rdflib.URIRef("has_part")),
            (rdflib.URIRef("ns2"), rdflib_cuba._default_rel,
             rdflib.URIRef("encloses"))
        })

    def test_parse_rdf(self):
        """Test parsing an rdf file."""
        self.graph.parse(CUBA_FILE, format="ttl")
        len_cuba = len(self.graph)
        self.assertRaises(TypeError, self.parser._parse_rdf,
                          ontology_file=RDF_FILE, namespaces={})
        self.assertRaises(TypeError, self.parser._parse_rdf,
                          namespaces={}, identifier="x")
        self.assertRaises(TypeError, self.parser._parse_rdf,
                          ontology_file=RDF_FILE, identifier="x")
        self.assertRaises(TypeError, self.parser._parse_rdf,
                          ontology_file=RDF_FILE, namespaces={},
                          identifier="x", invalid=True)
        with tempfile.NamedTemporaryFile() as f:
            self.parser._parse_rdf(
                identifier="parser_test",
                ontology_file=RDF_FILE,
                namespaces={
                    "parser_test": "http://www.osp-core.com/parser_test"
                },
                format="ttl",
                file=f
            )
        rdf = rdflib.Graph()
        rdf.parse(RDF_FILE, format="ttl")
        self.assertEqual(len(self.graph), len(rdf) + len_cuba)
        self.assertEqual(len(self.parser._graphs), 1)
        self.assertEqual(len(self.parser._graphs["parser_test"]), len(rdf))
        self.assertTrue(isomorphic(self.parser._graphs["parser_test"], rdf))
        self.assertIn(dict(self.graph.namespaces())["parser_test"],
                      rdflib.URIRef("http://www.osp-core.com/parser_test#"))

    def test_parse_yml(self):
        """Test parsing the yaml file."""
        invalid = dict(YML_DOC)
        invalid["identifier"] = "parser.test"
        self.assertRaises(ValueError, self.parser._parse_yml, invalid,
                          "/a/b/c/parser_test.yml", None)
        if os.name == "posix":
            result = self.parser._parse_yml(dict(YML_DOC),
                                            "/a/b/c/parser_test.yml", None)
            self.assertEqual(result["ontology_file"],
                             "/a/b/c/parser_test.ttl")
        else:
            result = self.parser._parse_yml(dict(YML_DOC),
                                            "C:\\a\\b\\parser_test.yml", None)
            self.assertEqual(result["ontology_file"],
                             "C:\\a\\b\\parser_test.ttl")

    @responses.activate
    def test_parse_yml_download(self):
        """Test downloading owl ontologies."""
        def request_callback(request):
            headers = {'request-id': '728d329e-0e86-11e4-a748-0c84dc037c13'}
            return (200, headers, "TEST FILE CONTENT")

        url = "http://my_ontology.com/ontology.owl"
        responses.add_callback(
            responses.GET, url,
            callback=request_callback,
            content_type='text/plain',
        )
        doc = dict(YML_DOC)
        doc["ontology_file"] = url
        with tempfile.NamedTemporaryFile(mode="wb+") as f:
            r = self.parser._parse_yml(doc, "/a/b/c/parser_test.yml", f)
            self.assertEqual(r["ontology_file"], f.name)
            f.seek(0)
            self.assertEqual(f.read(), b"TEST FILE CONTENT")

    def test_get_file_path(self):
        """Test the get_file_path method."""
        self.assertEqual(self.parser.get_file_path("test/my_file.yml"),
                         "test/my_file.yml")
        self.assertEqual(
            self.parser.get_file_path("my_file").lower(),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "my_file.yml"
            ))).lower()
        )
        self.assertEqual(
            self.parser.get_file_path("emmo").lower(),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "emmo.yml"
            ))).lower()
        )
        self.assertEqual(
            self.parser.get_file_path("city").lower(),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "city.ontology.yml"
            ))).lower()
        )

    def test_get_identifier(self):
        """Test the get_identifier method."""
        self.assertEqual(self.parser.get_identifier(YML_DOC), "parser_test")
        self.assertEqual(self.parser.get_identifier(YML_FILE), "parser_test")
        self.assertEqual(self.parser.get_identifier("parser_test"),
                         "parser_test")
        self.assertEqual(self.parser.get_identifier("emmo"), "emmo")

    def test_get_namespace_name(self):
        """Test the get_namespace_name method."""
        self.assertEqual(self.parser.get_namespace_names(YML_DOC),
                         ["parser_test"])
        self.assertEqual(self.parser.get_namespace_names(YML_FILE),
                         ["parser_test"])
        self.assertEqual(self.parser.get_namespace_names("parser_test"),
                         ["parser_test"])
        self.assertEqual(self.parser.get_namespace_names("emmo"),
                         ['mereotopology', 'physical', 'top', 'semiotics',
                          'perceptual', 'reductionistic', 'holistic',
                          'physicalistic', 'math', 'properties', 'materials',
                          'metrology', 'models', 'manufacturing', 'isq',
                          'siunits'])

    def test_get_requirements(self):
        """Test the get_requirements() method."""
        self.assertEqual(self.parser.get_requirements(YML_DOC), set())
        self.assertEqual(self.parser.get_requirements(YML_FILE), set())
        self.assertEqual(self.parser.get_requirements("parser_test"), {"city"})

    def test_store(self):
        """Test the store method."""
        self.parser.parse(YML_FILE)
        with tempfile.TemporaryDirectory() as destination:
            self.parser.store(destination)
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
                isomorphic(g, self.parser._graphs["parser_test"]))

    def test_parse(self):
        """Test the parse method."""
        self.parser.parse(YML_FILE)
        g1 = rdflib.Graph()
        g1.parse(CUBA_FILE, format="ttl")
        g1.parse(RDF_FILE, format="ttl")
        self.assertTrue(self.parser.graph, g1)
        g2 = rdflib.Graph()
        g2.parse(RDF_FILE, format="ttl")
        self.assertTrue(self.parser._graphs["parser_test"], [g1])
        self.assertEqual(len(self.parser._yaml_docs), 1)
        self.assertEqual(
            self.parser._yaml_docs[0]["ontology_file"].lower(),
            os.path.abspath(os.path.realpath(os.path.join(
                os.path.dirname(__file__), "parser_test.ttl"))).lower()
        )
        x = dict(self.parser._yaml_docs[0])
        x["ontology_file"] = YML_DOC["ontology_file"]
        self.assertEqual(x, YML_DOC)

    def test_add_reference_style_triples(self):
        """Test adding the reference style triples."""
        self.parser._add_reference_style_triples({
            "ns1": True,
            "ns2": False,
            "ns3": True
        })
        self.assertEqual(set(self.graph), {
            (rdflib.URIRef("ns1"), rdflib_cuba._reference_by_label,
             rdflib.Literal(True)),
            (rdflib.URIRef("ns3"), rdflib_cuba._reference_by_label,
             rdflib.Literal(True)),
        })


if __name__ == "__main__":
    unittest.main()
