"""This file provides the unittest for the YAML parser."""
import os
import yaml
import rdflib
import unittest2 as unittest
import logging
from rdflib.compare import isomorphic
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.ontology import Ontology
from osp.core.ontology.parser.parser import OntologyParser
from osp.core.ontology.parser.owl.parser import OWLParser
from osp.core.ontology.parser.yml.parser import YMLParser
from osp.core.ontology.parser import Parser
from osp.core.ontology.namespace_registry import NamespaceRegistry


YML_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "osp", "core", "ontology", "docs", "parser_test.ontology.yml"
)
CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")
EMMO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "emmo.yml")
RDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.ttl")
YML_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "parser_test.yml")


class TestYMLParser(unittest.TestCase):
    """Test cases for YAML parser."""

    def setUp(self):
        """Set up the test."""
        with open(YML_FILE, "r") as f:
            self.yml_doc = yaml.safe_load(f)
        self.ontology_doc = self.yml_doc["ontology"]
        self.namespace_registry = NamespaceRegistry()
        self.graph = self.namespace_registry._graph
        self.parser = YMLParser(YML_FILE)
        self.parser._ontology_doc = self.ontology_doc

    def test_validate_entity(self):
        """Test the validate_entity."""
        # everything should be fine
        for x, t, r in (
                ("relationshipB", rdflib.OWL.ObjectProperty, "relationship"),
                ("ClassD", rdflib.OWL.Class, "class"),
                ("attributeD", rdflib.OWL.DatatypeProperty, "attribute")):
            self.assertRaises(RuntimeError, self.parser._validate_entity,
                              x, self.ontology_doc[x])
            self.parser._graph.add((self.parser._get_iri(x),
                                    rdflib.RDF.type,
                                    t))
            result = self.parser._validate_entity(x, self.ontology_doc[x])
            self.assertEqual(r, result)

        # wrong type
        self.setUp()
        for x, t in (("relationshipB", rdflib.OWL.Class),
                     ("ClassD", rdflib.OWL.DatatypeProperty),
                     ("attributeD", rdflib.OWL.ObjectProperty)):
            self.assertRaises(RuntimeError, self.parser._validate_entity,
                              x, self.ontology_doc[x])
            self.parser._graph.add(
                (self.parser._get_iri(x), rdflib.RDF.type, t))
            self.assertRaises(ValueError, self.parser._validate_entity,
                              x, self.ontology_doc[x])

    def test_set_datatype(self):
        """Test the set_datatype method of the YAML parser."""
        for x, t in (("attributeA", rdflib.XSD.string),
                     ("attributeD", rdflib.XSD.float)):
            self.parser._set_datatype(x)
            self.assertEqual(list(self.parser._graph), [(
                self.parser._get_iri(x), rdflib.RDFS.range, t)])
            self.setUp()

        x = "attributeC"
        self.parser._set_datatype(x)
        self.assertEqual(len(self.parser._graph), 0)

        x = "attributeB"
        self.parser._set_datatype(x)
        self.assertEqual(set(self.parser._graph), {
            (self.parser._get_iri(x), rdflib.RDFS.range,
             rdflib_cuba["_datatypes/VECTOR-INT-2-2"]),
            (rdflib_cuba["_datatypes/VECTOR-INT-2-2"], rdflib.RDF.type,
             rdflib.RDFS.Datatype)})

    def test_check_default_rel_flag_on_entity(self):
        """Test the check_default_rel_flag_on_entity method."""
        self.parser._check_default_rel_flag_on_entity(
            "relationshipB",
            self.ontology_doc["relationshipB"]
        )
        self.assertEqual(list(self.parser._graph), [])
        self.parser._check_default_rel_flag_on_entity(
            "relationshipA",
            self.ontology_doc["relationshipA"]
        )
        # This is now done by the Ontology class.
        # self.assertEqual(set(self.parser._graph), {(
        #     self.parser._get_iri(), rdflib_cuba._default_rel,
        #     self.parser._get_iri("relationshipA")
        # )})

    def test_set_inverse(self):
        """Test the set_inverse method of the YAML parser."""
        self.parser._set_inverse("relationshipA",
                                 self.ontology_doc["relationshipA"])
        self.parser._set_inverse("relationshipB",
                                 self.ontology_doc["relationshipB"])
        self.assertEqual(list(self.parser._graph), [])
        self.parser._set_inverse("relationshipC",
                                 self.ontology_doc["relationshipC"])
        self.assertEqual(list(self.parser._graph), [(
            self.parser._get_iri("relationshipC"), rdflib.OWL.inverseOf,
            self.parser._get_iri("relationshipA")
        )])

    def test_add_attributes(self):
        """Test the add_attributes method of the YAML parser."""
        self.assertRaises(ValueError, self.parser._add_attributes,
                          "ClassA", self.ontology_doc["ClassA"])
        self.parser._parse_entity("attributeA",
                                  self.ontology_doc["attributeA"])

        # with default
        pre = set(self.parser._graph)
        self.parser._add_attributes("ClassA", self.ontology_doc["ClassA"])
        bnode1 = self.parser._graph.value(self.parser._get_iri("ClassA"),
                                  rdflib_cuba._default)
        bnode2 = self.parser._graph.value(None, rdflib.RDF.type,
                                  rdflib.OWL.Restriction)
        self.assertEqual(set(self.parser._graph) - pre, {
            (self.parser._get_iri("ClassA"), rdflib_cuba._default, bnode1),
            (bnode1, rdflib_cuba._default_value, rdflib.Literal("DEFAULT_A")),
            (bnode1, rdflib_cuba._default_attribute,
             self.parser._get_iri("attributeA")),
            (bnode2, rdflib.OWL.cardinality,
             rdflib.Literal(1, datatype=rdflib.XSD.integer)),
            (bnode2, rdflib.RDF.type, rdflib.OWL.Restriction),
            (self.parser._get_iri("ClassA"), rdflib.RDFS.subClassOf, bnode2),
            (bnode2, rdflib.OWL.onProperty, self.parser._get_iri("attributeA"))
        })

        # without default
        pre = set(self.parser._graph)
        self.parser._add_attributes("ClassE", self.ontology_doc["ClassE"])
        for s, _, _ in self.parser._graph.triples((None, rdflib.RDF.type,
                                                   rdflib.OWL.Restriction)):
            if s != bnode2:
                bnode3 = s

        self.assertEqual(set(self.parser._graph) - pre, {
            (bnode3, rdflib.OWL.onProperty,
             self.parser._get_iri("attributeA")),
            (bnode3, rdflib.OWL.cardinality,
             rdflib.Literal(1, datatype=rdflib.XSD.integer)),
            (bnode3, rdflib.RDF.type, rdflib.OWL.Restriction),
            (self.parser._get_iri("ClassE"), rdflib.RDFS.subClassOf, bnode3)
        })

    def test_add_type_triple(self):
        """Test the add_type_triple method of the YAML parser.."""
        iri = self.parser._get_iri("ClassA")

        # Class
        pre = set(self.parser._graph)
        self.parser._add_type_triple("ClassA", iri)
        self.assertEqual(set(self.parser._graph) - pre, {(
            iri, rdflib.RDF.type, rdflib.OWL.Class
        )})
        iri = self.parser._get_iri("ClassC")
        pre = set(self.parser._graph)
        self.parser._add_type_triple("ClassC", iri)
        self.assertEqual(set(self.parser._graph) - pre, {(
            iri, rdflib.RDF.type, rdflib.OWL.Class
        )})

        # Relationship
        iri = self.parser._get_iri("relationshipC")
        pre = set(self.parser._graph)
        self.parser._add_type_triple("relationshipC", iri)
        self.assertEqual(set(self.parser._graph) - pre, {(
            iri, rdflib.RDF.type, rdflib.OWL.ObjectProperty
        )})

        # Attribute
        iri = self.parser._get_iri("attributeB")
        pre = set(self.parser._graph)
        self.parser._add_type_triple("attributeB", iri)
        self.assertEqual(set(self.parser._graph) - pre, {
            (iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty),
            (iri, rdflib.RDF.type, rdflib.OWL.FunctionalProperty)
        })

    def test_add_superclass(self):
        """Test the add_superclass method of the YAML parser."""
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
        """Test the get_iri method of the YAML parser."""
        logging.getLogger(
            "osp.core.ontology.yml.yml_parser"
        ).addFilter(lambda record: False)
        self.parser._graph.parse(CUBA_FILE, format="ttl")
        self.assertEqual(
            self.parser._get_iri("Entity", "CUBA"),
            rdflib.term.URIRef('http://www.osp-core.com/cuba#Entity'))
        self.assertEqual(
            self.parser._get_iri("ENTITY", "CUBA"),
            rdflib.term.URIRef('http://www.osp-core.com/cuba#Entity'))
        self.assertEqual(
            self.parser._get_iri("ENTITY", "cuba"),
            rdflib.term.URIRef('http://www.osp-core.com/cuba#Entity'))
        self.assertEqual(
            self.parser._get_iri("entity", "CUBA"),
            rdflib.term.URIRef('http://www.osp-core.com/cuba#Entity'))
        self.assertRaises(AttributeError, self.parser._get_iri, "A", "B")
        self.parser._graph.add((
            rdflib.term.URIRef('http://www.osp-core.com/ns#MY_CLASS'),
            rdflib.RDF.type, rdflib.OWL.Class
        ))
        self.assertEqual(
            self.parser._get_iri("my_class", "NS"),
            rdflib.term.URIRef('http://www.osp-core.com/ns#MY_CLASS'))
        self.assertEqual(
            self.parser._get_iri("MY_CLASS", "NS"),
            rdflib.term.URIRef('http://www.osp-core.com/ns#MY_CLASS'))
        self.assertEqual(
            self.parser._get_iri("myClass", "ns"),
            rdflib.term.URIRef('http://www.osp-core.com/ns#MY_CLASS'))
        self.assertEqual(
            self.parser._get_iri("MyClass", "NS"),
            rdflib.term.URIRef('http://www.osp-core.com/ns#MY_CLASS'))

        # no entity name --> no checks
        self.assertEqual(self.parser._get_iri(None, "B"),
                         rdflib.term.URIRef('http://www.osp-core.com/b#'))
        self.assertEqual(self.parser._get_iri(None, "b"),
                         rdflib.term.URIRef('http://www.osp-core.com/b#'))

    def test_load_entity(self):
        """Test the load_entity method of the YAML parser."""
        # load class
        name = "ClassA"
        self.parser._graph.parse(CUBA_FILE, format="ttl")
        pre = set(self.parser._graph)
        self.parser._parse_entity(name, self.ontology_doc[name])
        iri = self.parser._get_iri(name)
        self.assertEqual(set(self.parser._graph) - pre, {
            (iri, rdflib.RDF.type, rdflib.OWL.Class),
            (iri, rdflib.RDFS.isDefinedBy,
             rdflib.term.Literal("Class A", lang="en")),
            (iri, rdflib.RDFS.subClassOf, rdflib_cuba.Entity),
            (iri, rdflib.SKOS.prefLabel,
             rdflib.term.Literal("ClassA", lang="en"))
        })

        # load relationship
        name = "relationshipA"
        self.parser._graph.parse(CUBA_FILE, format="ttl")
        pre = set(self.parser._graph)
        self.parser._parse_entity(name, self.ontology_doc[name])
        iri = self.parser._get_iri(name)
        self.assertEqual(set(self.parser._graph) - pre, {
            (iri, rdflib.RDF.type, rdflib.OWL.ObjectProperty),
            (iri, rdflib.RDFS.subPropertyOf, rdflib_cuba.activeRelationship),
            (iri, rdflib.SKOS.prefLabel,
             rdflib.term.Literal("relationshipA", lang="en"))
        })

        # load attribute
        name = "attributeA"
        self.parser._graph.parse(CUBA_FILE, format="ttl")
        pre = set(self.parser._graph)
        self.parser._parse_entity(name, self.ontology_doc[name])
        iri = self.parser._get_iri(name)
        self.assertEqual(set(self.parser._graph) - pre, {
            (iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty),
            (iri, rdflib.RDF.type, rdflib.OWL.FunctionalProperty),
            (iri, rdflib.RDFS.subPropertyOf, rdflib_cuba.attribute),
            (iri, rdflib.SKOS.prefLabel,
             rdflib.term.Literal("attributeA", lang="en"))
        })

    def test_split_name(self):
        """Test the split_name method of the YAML parser."""
        self.assertEqual(("a", "B"), self.parser.split_name("A.B"))
        self.assertEqual(("a", "b"), self.parser.split_name("a.b"))
        self.assertRaises(ValueError, self.parser.split_name, "B")

    def test_parse(self):
        """Test the parse method of the YAML parser."""
        ontology_yml = Ontology(from_parser=YMLParser(YML_FILE))
        ontology_owl = Ontology(from_parser=OWLParser(YML_CONFIG_FILE))
        self.assertTrue(isomorphic(ontology_owl.graph, ontology_yml.graph))
        self.assertEqual(self.parser._file_path, YML_FILE)
        self.assertEqual(self.parser._namespace, "parser_test")


if __name__ == "__main__":
    unittest.main()
