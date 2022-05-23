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
        emmo_namespaces = {
            "annotations": "http://emmo.info/emmo/top/annotations#",
            "holistic": "http://emmo.info/emmo/middle/holistic#",
            "isq": "http://emmo.info/emmo/middle/isq#",
            "manufacturing": "http://emmo.info/emmo/middle/manufacturing#",
            "materials": "http://emmo.info/emmo/middle/materials#",
            "math": "http://emmo.info/emmo/middle/math#",
            "meretopology": "http://emmo.info/emmo/top/mereotopology#",
            "metrology": "http://emmo.info/emmo/middle/metrology#",
            "models": "http://emmo.info/emmo/middle/models#",
            "perceptual": "http://emmo.info/emmo/middle/perceptual#",
            "physical": "http://emmo.info/emmo/top/physical#",
            "physicalistic": "http://emmo.info/emmo/middle/physicalistic#",
            "properties": "http://emmo.info/emmo/middle/properties#",
            "reductionistic": "http://emmo.info/emmo/middle/reductionistic#",
            "semiotics": "http://emmo.info/emmo/middle/semiotics#",
            "siunits": "http://emmo.info/emmo/middle/siunits#",
            "top": "http://emmo.info/emmo/top#",
        }
        expected_namespaces = dict()
        for nss in (
            required_namespaces,
            foaf_namespaces,
            dcat2_namespaces,
            emmo_namespaces,
            city_namespaces,
        ):
            expected_namespaces.update(nss)
        self.assertSetEqual(
            set(
                OntologyNamespace(iri=iri, name=name, ontology=self.ontology)
                for name, iri in expected_namespaces.items()
            ),
            set(self.ontology.namespaces),
        )

        # Check that names of the namespaces were loaded.
        self.assertSetEqual(
            set(expected_namespaces.keys()),
            set(ns.name for ns in self.ontology.namespaces),
        )

        # Check that the default relationships were properly loaded.
        expected_default_relationships = {
            OntologyNamespace(
                iri=iri, name=name, ontology=self.ontology
            ): OntologyRelationship(
                uid=UID(
                    "http://emmo.info/emmo/top/mereotopology#"
                    "EMMO_17e27c22_37e1_468c_9dd7_95e137f73e7f"
                ),
                session=self.ontology,
            )
            for name, iri in emmo_namespaces.items()
        }
        expected_default_relationships.update(
            {
                OntologyNamespace(
                    iri="https://www.simphony-project.eu/city#",
                    name="city",
                    ontology=self.ontology,
                ): OntologyRelationship(
                    uid=UID("https://www.simphony-project.eu/city#hasPart"),
                    session=self.ontology,
                )
            }
        )
        expected_default_relationships.update(
            {
                OntologyNamespace(
                    iri="http://www.w3.org/2002/07/owl#",
                    name="owl",
                    ontology=self.ontology,
                ): OntologyRelationship(
                    uid=UID("http://www.w3.org/2002/07/owl#topObjectProperty"),
                    session=self.ontology,
                )
            }
        )
        self.assertDictEqual(
            expected_default_relationships, self.ontology.default_relationships
        )

        # Check that the active relationships were properly loaded.
        self.assertSetEqual(
            {
                OntologyRelationship(
                    uid=UID(
                        "http://emmo.info/emmo/top/mereotopology#"
                        "EMMO_8c898653_1118_4682_9bbf_6cc334d16a99"
                    ),
                    session=self.ontology,
                ),
                OntologyRelationship(
                    uid=UID(
                        "http://emmo.info/emmo/middle/semiotics#"
                        "EMMO_60577dea_9019_4537_ac41_80b0fb563d41"
                    ),
                    session=self.ontology,
                ),
                OntologyRelationship(
                    uid=UID(
                        "https://www.simphony-project.eu/"
                        "simphony#activeRelationship"
                    ),
                    session=self.ontology,
                ),
                OntologyRelationship(
                    uid=UID("https://www.simphony-project.eu/city#encloses"),
                    session=self.ontology,
                ),
            },
            set(self.ontology.active_relationships),
        )

        # Check that the reference styles were properly loaded.
        self.assertDictEqual(
            {
                OntologyNamespace(
                    iri=iri, name=name, ontology=self.ontology
                ): True
                if name in emmo_namespaces
                else False
                for name, iri in expected_namespaces.items()
            },
            self.ontology.reference_styles,
        )

        # Try to fetch all the namespaces by name.
        self.assertSetEqual(
            set(self.ontology.namespaces),
            set(
                self.ontology.get_namespace(name)
                for name in expected_namespaces
            ),
        )
