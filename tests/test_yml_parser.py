import os
import yaml
import rdflib
import unittest2 as unittest
from osp.core.ontology.yml.yml_parser import YmlParser

YML_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "osp", "core", "ontology", "docs", "parser_test.ontology.yml"
)


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
        self.setUp()

        # wrong type
        for x, t in (
                ("relationshipB", rdflib.OWL.Class),
                ("ClassD", rdflib.OWL.DatatypeProperty),
                ("attributeD", rdflib.OWL.ObjectProperty)):
            self.assertRaises(RuntimeError, self.parser._validate_entity,
                              x, self.ontology_doc[x])
            self.graph.add((self.parser._get_iri(x), rdflib.RDF.type, t))
            self.assertRaises(ValueError, self.parser._validate_entity,
                              x, self.ontology_doc[x])


if __name__ == "__main__":
    unittest.main()
