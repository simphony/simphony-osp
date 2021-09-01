"""Test the ontology class."""

import unittest

from rdflib import URIRef, Graph, Literal, RDF, RDFS, OWL

from osp.core.ontology.cuba import cuba_namespace
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.ontology import Ontology
from osp.core.ontology.parser.owl.parser import OWLParser


class TestOntology(unittest.TestCase):
    """Test the ontology class."""

    def setUp(self):
        """Set up Graph and Parser."""
        self.ontology = Ontology(identifier='identifier')
        self.graph = self.ontology._ontology_graph
        self.overlay = self.ontology._overlay

    def test_overlay_cuba_triples(self):
        """Test adding the cuba triples, like active relationships."""
        self.graph.add((URIRef("has_part"), RDF.type,
                        OWL.ObjectProperty))
        self.graph.add((URIRef("encloses"), RDF.type,
                        OWL.ObjectProperty))
        self.ontology.active_relationships = (URIRef("has_part"),
                                              URIRef("encloses"))
        self.ontology._update_overlay()
        self.assertEqual(set(self.ontology.graph) - set(self.graph), {
            (URIRef("encloses"), RDFS.subPropertyOf,
             cuba_namespace.activeRelationship),
            (URIRef("has_part"), RDFS.subPropertyOf,
             cuba_namespace.activeRelationship)
        })

    def test_overlay_default_rel_triples(self):
        """Test adding the default rel triples."""
        self.ontology.namespaces = {'ns1': URIRef('ns1')}
        self.ontology.default_relationship = URIRef("has_part")
        self.ontology._update_overlay()
        self.assertIn(
            (URIRef("ns1"), cuba_namespace._default_rel,
             URIRef("has_part")),
            self.ontology.graph
        )

    def test_reference_style_triples(self):
        """Test adding the reference style triples."""
        for value in (True, False):
            self.ontology.namespaces = {'ns1': URIRef('ns1')}
            self.ontology.reference_style = value
            self.ontology._update_overlay()
            self.assertIn((URIRef('ns1'), cuba_namespace._reference_by_label,
                           Literal(value)),
                          self.ontology.graph)
            self.assertNotIn((URIRef('ns1'), cuba_namespace._reference_by_label,
                              Literal(not value)),
                             self.ontology.graph)


class TestFoaf(unittest.TestCase):
    """Test the ontology class."""

    def setUp(self):
        """Set up Graph and Parser."""
        foaf_parser = OWLParser('test_ontology_foaf.yml')
        self.ontology = Ontology(from_parser=foaf_parser)

    def test_example(self):
        # Get relationships, attributes, classes.
        member = self.ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/member'))
        self.assertTrue(isinstance(member, OntologyRelationship))
        knows = self.ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/knows'))
        self.assertTrue(isinstance(knows, OntologyRelationship))
        name = self.ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/name'))
        self.assertTrue(isinstance(name, OntologyAttribute))
        # person = self.ontology.from_identifier(
        #     URIRef('http://xmlns.com/foaf/0.1/Person'))
        # self.assertTrue(isinstance(person, OntologyClass))

        # Active relationships
        self.assertIn(member, self.ontology.active_relationships)
        self.ontology.active_relationships = (knows, )
        self.assertIn(knows, self.ontology.active_relationships)
        self.assertNotIn(member, self.ontology.active_relationships)
        self.ontology.active_relationships = (knows, member)
        self.assertIn(knows, self.ontology.active_relationships)
        self.assertIn(member, self.ontology.active_relationships)
        self.ontology.active_relationships = (member, )

        # Default relationship
        self.assertEqual(self.ontology.default_relationship, knows)
        self.ontology.default_relationship = member
        self.assertEqual(self.ontology.default_relationship, member)
        self.ontology.default_relationship = None
        self.assertIs(self.ontology.default_relationship, None)
        self.ontology.default_relationship = knows
        self.assertEqual(self.ontology.default_relationship, knows)

        # Reference style
        self.assertFalse(self.ontology.reference_style)
        self.ontology.reference_style = True
        self.assertTrue(self.ontology.reference_style)
        self.ontology.reference_style = False
        self.assertFalse(self.ontology.reference_style)

        # Graph
        self.assertTrue(isinstance(self.ontology.graph, Graph))

        # Get and test namespace.
        foaf_namespace = self.ontology.get_namespace('foaf')
        self.assertEqual(foaf_namespace.name, 'foaf')
        self.assertEqual(foaf_namespace.iri,
                         URIRef('http://xmlns.com/foaf/0.1/'))
        member = self.ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/member'))
        self.assertEqual(getattr(foaf_namespace, 'member'), member)
        self.assertRaises(KeyError,
                          lambda x: foaf_namespace[x],
                          'member')
        self.assertIn('birthday', dir(foaf_namespace))


if __name__ == "__main__":
    unittest.main()
