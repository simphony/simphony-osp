"""Test the `simphony_osp.session` module."""

import unittest

from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.utils.datatypes import UID


class TestLoadParsers(unittest.TestCase):
    """Test merging ontology packages in the ontology."""

    def setUp(self) -> None:
        """Set up ontology."""
        self.ontology = Session(identifier="some_ontology", ontology=True)

    def test_loading_packages(self):
        """Test merging several ontology packages."""
        parsers = (
            OntologyParser.get_parser("foaf"),
            OntologyParser.get_parser("emmo"),
            OntologyParser.get_parser("dcat2"),
            OntologyParser.get_parser("city"),
        )
        for parser in parsers:
            self.ontology.load_parser(parser)

        # Test that all namespaces were loaded.
        required_namespaces = {
            "simphony": "https://www.simphony-project.eu/simphony#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
        }
        city_namespaces = {"city": "https://www.simphony-project.eu/city#"}
        foaf_namespaces = {"foaf": "http://xmlns.com/foaf/0.1/"}
        dcat2_namespaces = {"dcat2": "http://www.w3.org/ns/dcat#"}
        emmo_namespaces = {"emmo": "http://emmo.info/emmo#"}
        expected_namespaces = dict()
        for nss in (
            required_namespaces,
            foaf_namespaces,
            dcat2_namespaces,
            emmo_namespaces,
            city_namespaces,
        ):
            expected_namespaces.update(nss)
        self.assertDictEqual(
            expected_namespaces,
            {ns.name: str(ns.iri) for ns in self.ontology.namespaces},
        )

        # Check that names of the namespaces were loaded.
        self.assertSetEqual(
            set(expected_namespaces.keys()),
            set(ns.name for ns in self.ontology.namespaces),
        )

        # Try to fetch all the namespaces by name.
        self.assertSetEqual(
            set(self.ontology.namespaces),
            set(
                self.ontology.get_namespace(name)
                for name in expected_namespaces
            ),
        )
