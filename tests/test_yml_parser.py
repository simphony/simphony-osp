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
        iri = self.parser._get_iri("ClassA")
        self.assertRaises(ValueError, self.parser._add_type_triple, "ClassA",
                          iri)
        self.graph.parse(CUBA_FILE, format="ttl")

        # Class
        pre = set(self.graph)
        self.parser._add_type_triple("ClassA", iri)
        self.assertEqual(set(self.graph) - pre, {(
            iri, rdflib.RDF.type, rdflib.OWL.Class
        )})
        iri = self.parser._get_iri("ClassC")
        pre = set(self.graph)
        self.parser._add_type_triple("ClassC", iri)
        self.assertEqual(set(self.graph) - pre, {(
            iri, rdflib.RDF.type, rdflib.OWL.Class
        )})

        # Relationship
        iri = self.parser._get_iri("relationshipC")
        pre = set(self.graph)
        self.parser._add_type_triple("relationshipC", iri)
        self.assertEqual(set(self.graph) - pre, {(
            iri, rdflib.RDF.type, rdflib.OWL.ObjectProperty
        )})

        # Attribute
        iri = self.parser._get_iri("attributeB")
        pre = set(self.graph)
        self.parser._add_type_triple("attributeB", iri)
        self.assertEqual(set(self.graph) - pre, {
            (iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty),
            (iri, rdflib.RDF.type, rdflib.OWL.FunctionalProperty)
        })

    def test_add_superclass(self):
        iri = self.parser._get_iri("ClassD")
        self.assertRaises(AttributeError, self.parser._add_superclass,
                          "ClassD", iri, "parser_test.Invalid")
        self.assertRaises(AttributeError, self.parser._add_superclass,
                          "ClassD", iri, "cuba.Invalid")
        self.assertRaises(AttributeError, self.parser._add_superclass,
                          "ClassD", iri, "invalid.ClassA")
        self.parser._add_superclass("ClassD", iri, "parser_test.ClassA")
        iri = self.parser._get_iri("relationshipB")
        self.parser._add_superclass("relationshipB", iri,
                                    "parser_test.relationshipA")
        iri = self.parser._get_iri("attributeB")
        self.parser._add_superclass("attributeB", iri,
                                    "parser_test.attributeA")

    def test_get_iri(self):
        self.assertEqual(self.parser._get_iri("A", "B"),
                         rdflib.term.URIRef('http://www.osp-core.com/B#A'))
        self.assertEqual(self.parser._get_iri(None, "B"),
                         rdflib.term.URIRef('http://www.osp-core.com/B#'))
        self.assertEqual(
            self.parser._get_iri("A", None),
            rdflib.term.URIRef('http://www.osp-core.com/parser_test#A'))
        self.assertEqual(
            self.parser._get_iri(None, None), 
            rdflib.term.URIRef('http://www.osp-core.com/parser_test#'))

    def test_load_entity(self):
        self.graph.parse(CUBA_FILE, format="ttl")

if __name__ == "__main__":
    unittest.main()
