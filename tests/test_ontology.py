import unittest
from rdflib import URIRef, Literal, RDF, RDFS, OWL
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.ontology import Ontology


class TestOntology(unittest.TestCase):
    
    def setUp(self):
        """Set up Graph and Parser."""
        self.ontology = Ontology(identifier='identifier')
        self.graph = self.ontology._ontology_graph
        self.overlay = self.ontology._ontology_overlay

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
             rdflib_cuba.activeRelationship),
            (URIRef("has_part"), RDFS.subPropertyOf,
             rdflib_cuba.activeRelationship)
        })

    def test_overlay_default_rel_triples(self):
        """Test adding the default rel triples."""
        self.ontology.namespaces = {'ns1': URIRef('ns1')}
        self.ontology.default_relationship = URIRef("has_part")
        self.ontology._update_overlay()
        self.assertIn(
            (URIRef("ns1"), rdflib_cuba._default_rel,
             URIRef("has_part")),
            self.ontology.graph
        )

    def test_reference_style_triples(self):
        """Test adding the reference style triples."""
        for value in (True, False):
            self.ontology.namespaces = {'ns1': URIRef('ns1')}
            self.ontology.reference_style = value
            self.ontology._update_overlay()
            self.assertIn((URIRef('ns1'), rdflib_cuba._reference_by_label,
                           Literal(value)),
                          self.ontology.graph)
            self.assertNotIn((URIRef('ns1'), rdflib_cuba._reference_by_label,
                              Literal(not value)),
                             self.ontology.graph)


if __name__ == "__main__":
    unittest.main()
