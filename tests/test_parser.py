import os
import yaml
import rdflib
import unittest2 as unittest
import tempfile
from rdflib.compare import isomorphic
from osp.core.ontology.parser import Parser
from osp.core.ontology.cuba import rdflib_cuba


RDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.ttl")
CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")
YML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.yml")
with open(YML_FILE) as f:
    YML_DOC = yaml.safe_load(f)


class TestParser(unittest.TestCase):
    def setUp(self):
        self.graph = rdflib.Graph()
        self.parser = Parser(self.graph)

    def test_add_cuba_triples(self):
        self.parser._add_cuba_triples([
            rdflib.URIRef("has_part"), rdflib.URIRef("encloses")
        ])
        self.assertEqual(set(self.graph), {
            (rdflib.URIRef("encloses"), rdflib.RDFS.subPropertyOf,
             rdflib_cuba.activeRelationship),
            (rdflib.URIRef("has_part"), rdflib.RDFS.subPropertyOf,
             rdflib_cuba.activeRelationship)
        })

    def test_add_default_rel_triples(self):
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
        self.parser._parse_rdf(
            identifier="parser_test",
            ontology_file=RDF_FILE,
            namespaces={
                "parser_test": "http://www.osp-core.com/parser_test"
            },
            format="ttl"
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
        invalid = dict(YML_DOC)
        invalid["identifier"] = "parser.test"
        self.assertRaises(ValueError, self.parser._parse_yml, invalid,
                          "/a/b/c/parser_test.yml")
        result = self.parser._parse_yml(dict(YML_DOC),
                                        "/a/b/c/parser_test.yml")
        self.assertEqual(result["ontology_file"],
                         "/a/b/c/parser_test.ttl")

    def test_get_file_path(self):
        self.assertEqual(self.parser.get_file_path("test/my_file.yml"),
                         "test/my_file.yml")
        self.assertEqual(
            self.parser.get_file_path("my_file"),
            os.path.abspath(os.path.relpath(os.path.join(
                os.path.dirname(__file__), "..", "osp", "core", "ontology",
                "docs", "my_file.ontology.yml"
            )))
        )

    def test_get_identifier(self):
        self.assertEqual(self.parser.get_identifier(YML_DOC), "parser_test")
        self.assertEqual(self.parser.get_identifier(YML_FILE), "parser_test")
        self.assertEqual(self.parser.get_identifier("parser_test"),
                         "parser_test")

    def test_store(self):
        self.parser.parse(YML_FILE)
        with tempfile.TemporaryDirectory() as destination:
            self.parser.store(destination)
            self.assertEqual(os.listdir(destination),
                             ["parser_test.ttl", "parser_test.yml"])
            with open(os.path.join(destination, "parser_test.yml")) as f:
                yml_doc = yaml.safe_load(f)
                self.assertEqual(yml_doc["ontology_file"], "parser_test.ttl")
                yml_doc["ontology_file"] = YML_DOC["ontology_file"]
                self.assertEqual(yml_doc, YML_DOC)
            g = rdflib.Graph()
            g.parse(os.path.join(destination, "parser_test.ttl"),
                    format="ttl")
            self.assertTrue(
                isomorphic(g, self.parser._graphs["parser_test"]))

    def test_parse(self):
        self.parser.parse(YML_FILE)
        g1 = rdflib.Graph()
        g1.parse(CUBA_FILE, format="ttl")
        g1.parse(RDF_FILE, format="ttl")
        self.assertTrue(self.parser.graph, g1)
        g2 = rdflib.Graph()
        g2.parse(RDF_FILE, format="ttl")
        self.assertTrue(self.parser._graphs["parser_test"], [g1])
        self.assertEqual(len(self.parser._yaml_docs), 1)
        self.assertEqual(self.parser._yaml_docs[0]["ontology_file"], 
            os.path.abspath(os.path.realpath(os.path.join(
                os.path.dirname(__file__), "parser_test.ttl"))))
        x = dict(self.parser._yaml_docs[0])
        x["ontology_file"] = YML_DOC["ontology_file"]
        self.assertEqual(x, YML_DOC)


if __name__ == "__main__":
    unittest.main()
