import rdflib
import unittest2 as unittest
from osp.core.ontology.parser import Parser
from osp.core.ontology.cuba import rdflib_cuba


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


if __name__ == "__main__":
    unittest.main()
