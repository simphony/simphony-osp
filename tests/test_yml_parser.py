import os
import yaml
import rdflib
import unittest2 as unittest
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.yml.yml_parser import YmlParser

YML_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "osp", "core", "ontology", "docs", "parser_test.ontology.yml"
)
CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")


class TestYmlParser(unittest.TestCase):
    def setUp(self):
        with open(YML_FILE, "r") as f:
            self.yml_doc = yaml.safe_load(f)
        self.ontology_doc = self.yml_doc["ontology"]
        self.graph = rdflib.Graph()
        self.parser = YmlParser(self.graph)
        self.parser._namespace = "parser_test"
        self.parser._ontology_doc = self.ontology_doc
        self.parser._doc = self.yml_doc
        self.parser._file_path = YML_FILE

    def test_validate_entity(self):
        # everything should be fine
        for x, t, r in (
                ("relationshipB", rdflib.OWL.ObjectProperty, "relationship"),
                ("ClassD", rdflib.OWL.Class, "class"),
                ("attributeD", rdflib.OWL.DatatypeProperty, "attribute")):
            self.assertRaises(RuntimeError, self.parser._validate_entity,
                              x, self.ontology_doc[x])
            self.graph.add((self.parser._get_iri(x), rdflib.RDF.type, t))
            result = self.parser._validate_entity(x, self.ontology_doc[x])
            self.assertEqual(r, result)

        # wrong type
        self.setUp()
        for x, t in (("relationshipB", rdflib.OWL.Class),
                     ("ClassD", rdflib.OWL.DatatypeProperty),
                     ("attributeD", rdflib.OWL.ObjectProperty)):
            self.assertRaises(RuntimeError, self.parser._validate_entity,
                              x, self.ontology_doc[x])
            self.graph.add((self.parser._get_iri(x), rdflib.RDF.type, t))
            self.assertRaises(ValueError, self.parser._validate_entity,
                              x, self.ontology_doc[x])

    def test_set_datatype(self):
        for x, t in (("attributeA", rdflib.XSD.string),
                     ("attributeD", rdflib.XSD.float)):
            self.parser._set_datatype(x, self.ontology_doc[x])
            self.assertEqual(list(self.graph), [(
                self.parser._get_iri(x), rdflib.RDFS.range, t)])
            self.setUp()

        x = "attributeC"
        self.parser._set_datatype(x, self.ontology_doc[x])
        self.assertEqual(len(self.graph), 0)

        x = "attributeB"
        self.parser._set_datatype(x, self.ontology_doc[x])
        self.assertEqual(set(self.graph), {
            (self.parser._get_iri(x), rdflib.RDFS.range,
             rdflib_cuba["datatypes/VECTOR-INT-2-2"]),
            (rdflib_cuba["datatypes/VECTOR-INT-2-2"], rdflib.RDF.type,
             rdflib.RDFS.Datatype)})

    def test_check_default_rel(self):
        self.parser._check_default_rel("relationshipB",
                                       self.ontology_doc["relationshipB"])
        self.assertEqual(list(self.graph), [])
        self.parser._check_default_rel("relationshipA",
                                       self.ontology_doc["relationshipA"])
        self.assertEqual(set(self.graph), {(
            self.parser._get_iri(), rdflib_cuba._default_rel,
            self.parser._get_iri("relationshipA")
        )})

    def test_set_inverse(self):
        self.parser._set_inverse("relationshipA",
                                 self.ontology_doc["relationshipA"])
        self.parser._set_inverse("relationshipB",
                                 self.ontology_doc["relationshipB"])
        self.assertEqual(list(self.graph), [])
        self.parser._set_inverse("relationshipC",
                                 self.ontology_doc["relationshipC"])
        self.assertEqual(list(self.graph), [(
            self.parser._get_iri("relationshipC"), rdflib.OWL.inverseOf,
            self.parser._get_iri("relationshipA")
        )])

    def test_add_attributes(self):
        self.graph.parse(CUBA_FILE, format="ttl")
        self.assertRaises(ValueError, self.parser._add_attributes,
                          "ClassA", self.ontology_doc["ClassA"])
        self.parser._load_entity("attributeA", self.ontology_doc["attributeA"])

        # with default
        pre = set(self.graph)
        self.parser._add_attributes("ClassA", self.ontology_doc["ClassA"])
        bnode = self.graph.value(self.parser._get_iri("ClassA"),
                                 rdflib_cuba._default)
        self.assertEqual(set(self.graph) - pre, {
            (self.parser._get_iri("ClassA"), rdflib_cuba._default, bnode),
            (bnode, rdflib_cuba._default_value, rdflib.Literal("DEFAULT_A")),
            (bnode, rdflib_cuba._default_attribute,
             self.parser._get_iri("attributeA")),
            (self.parser._get_iri("attributeA"),
             rdflib.RDFS.domain, self.parser._get_iri("ClassA"))
        })

        # without default
        pre = set(self.graph)
        self.parser._add_attributes("ClassE", self.ontology_doc["ClassE"])
        self.assertEqual(set(self.graph) - pre, {
            (self.parser._get_iri("attributeA"),
             rdflib.RDFS.domain, self.parser._get_iri("ClassE"))
        })

    def test_add_type_triple(self):
        self.assertRaises(ValueError, self.parser._add_type_triple, "ClassA",
                          self.ontology_doc["ClassA"])


if __name__ == "__main__":
    unittest.main()
