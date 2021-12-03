"""Test the ontology class."""

import tempfile
import unittest
from decimal import Decimal
from typing import Hashable

from rdflib import RDFS, XSD, Graph, Literal, URIRef

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.utils.datatypes import UID
from osp.core.ontology.annotation import OntologyAnnotation
from osp.core.ontology.individual import OntologyIndividual
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.parser.owl.parser import OWLParser
from osp.core.ontology.parser.yml.parser import YMLParser
from osp.core.session.session import Session


class TestFOAFOntology(unittest.TestCase):
    """Tests classes related to the ontology management using FOAF ontology."""

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and FOAF.
        """
        with tempfile.NamedTemporaryFile('w', suffix='.yml', delete=False) \
                as file:
            foaf_modified: str = """
            active_relationships:
              - http://xmlns.com/foaf/0.1/member
            default_relationship: http://xmlns.com/foaf/0.1/knows
            format: xml
            identifier: foaf
            namespaces:
              foaf: http://xmlns.com/foaf/0.1/
            ontology_file: http://xmlns.com/foaf/spec/index.rdf
            reference_by_label: false
            """
            file.write(foaf_modified)
            file.seek(0)
            yml_path = file.name

        cls.ontology = Session(identifier='test-tbox', ontology=True)
        for parser in (OWLParser('cuba'), OWLParser('owl'), OWLParser('rdfs'),
                       OWLParser(yml_path)):
            cls.ontology.load_parser(parser)
        cls.prev_default_ontology = Session.ontology
        Session.ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def test_ontology(self):
        """Tests the Session class used as an ontology."""
        ontology = self.ontology

        # Get relationships, attributes and classes with `from_identifier`
        # method of `Session objects`.
        member = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/member'))
        self.assertTrue(isinstance(member, OntologyRelationship))
        knows = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/knows'))
        self.assertTrue(isinstance(knows, OntologyRelationship))
        name = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/name'))
        self.assertTrue(isinstance(name, OntologyAttribute))

        # Test `active_relationships property`.
        self.assertIn(member, ontology.active_relationships)
        ontology.active_relationships = (knows, )
        self.assertIn(knows, ontology.active_relationships)
        self.assertNotIn(member, ontology.active_relationships)
        ontology.active_relationships = (knows, member)
        self.assertIn(knows, ontology.active_relationships)
        self.assertIn(member, ontology.active_relationships)
        ontology.active_relationships = (member, )

        # Test the `get_namespace` method.
        self.assertRaises(KeyError, ontology.get_namespace, 'fake')
        foaf_namespace = ontology.get_namespace('foaf')
        self.assertTrue(isinstance(foaf_namespace, OntologyNamespace))
        self.assertEqual(foaf_namespace.name, 'foaf')
        self.assertEqual(foaf_namespace.iri,
                         URIRef('http://xmlns.com/foaf/0.1/'))

        # Test `default_relationship` property.
        self.assertIn(knows, ontology.default_relationships.values())
        ontology.default_relationships = {foaf_namespace: member}
        self.assertIn(member, ontology.default_relationships.values())
        ontology.default_relationships = None
        self.assertDictEqual(ontology.default_relationships, dict())
        ontology.default_relationships = {foaf_namespace: knows}
        self.assertIn(knows, ontology.default_relationships.values())

        # Test `reference_styles` property.
        self.assertFalse(ontology.reference_styles[foaf_namespace])
        ontology.reference_styles = {foaf_namespace: True}
        self.assertTrue(ontology.reference_styles[foaf_namespace])
        ontology.reference_styles = {foaf_namespace: False}
        self.assertFalse(ontology.reference_styles[foaf_namespace])

        # Test the `graph` property.
        self.assertTrue(isinstance(ontology.graph, Graph))

    def test_attribute(self):
        """Tests the OntologyAttribute subclass.

        Includes methods inherited from OntologyEntity.
        """
        ontology = self.ontology

        # Test with foaf:name attribute.
        name = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/name'))
        self.assertTrue(isinstance(name, OntologyAttribute))

        # Test `uid` property.
        self.assertEqual(name.uid,
                         UID(URIRef('http://xmlns.com/foaf/0.1/name')))
        name.uid = UID(URIRef('http://xmlns.com/foaf/0.1/other_name'))
        self.assertEqual(name.uid,
                         UID(URIRef('http://xmlns.com/foaf/0.1/other_name')))
        name.uid = UID(URIRef('http://xmlns.com/foaf/0.1/name'))

        # Test `identifier property`.
        self.assertEqual(name.identifier,
                         URIRef('http://xmlns.com/foaf/0.1/name'))

        # Test `iri` property.
        self.assertEqual(name.iri,
                         URIRef('http://xmlns.com/foaf/0.1/name'))

        # Test `label` property.
        self.assertEqual(str, type(name.label))
        self.assertEqual('name', name.label)

        # Test `label_lang` property.
        self.assertIsNone(name.label_lang)

        # Test 'label_literal' property.
        self.assertEqual(Literal('name'), name.label_literal)

        # Test `iter_labels` method.
        # Test `lang = None`, `return_prop = False`, `return_literal = True`.
        self.assertTupleEqual((Literal('name'), ), tuple(name.iter_labels()))
        # Test `lang = "en"`, `return_prop = False`, `return_literal = True`.
        self.assertTupleEqual(tuple(), tuple(name.iter_labels(lang='en')))
        # Test `lang = None`, `return_prop = True`, `return_literal = True`.
        self.assertTupleEqual(((Literal('name'), URIRef(RDFS.label)),),
                              tuple(name.iter_labels(return_prop=True)))
        # Test `lang = None`, `return_prop = True`, `return_literal = False`.
        self.assertTupleEqual((('name', URIRef(RDFS.label)),),
                              tuple(name.iter_labels(
                                  return_literal=False,
                                  return_prop=True)))
        # Test `lang = None`, `return_prop = False`, `return_literal = False`.
        self.assertTupleEqual(('name', ),
                              tuple(name.iter_labels(
                                  return_literal=False,
                                  return_prop=False)))

        # Test `session` property.
        self.assertIs(name.session, ontology)
        # TODO: Test setter.

        # Test `direct_superclasses` property.
        self.assertSetEqual(set(), name.direct_superclasses)

        # Test `direct_subclasses` property.
        self.assertSetEqual(set(), name.direct_subclasses)

        # Test `superclasses` property.
        self.assertSetEqual({name}, name.superclasses)

        # Test `subclasses` property.
        self.assertSetEqual({name}, name.subclasses)

        # Test `triples` property.
        self.assertSetEqual({
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#label'),
             Literal('name')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
             URIRef('http://www.w3.org/2002/07/owl#DatatypeProperty')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
             URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#Property')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#domain'),
             URIRef('http://www.w3.org/2002/07/owl#Thing')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#comment'),
             Literal('A name for some thing.')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#isDefinedBy'),
             URIRef('http://xmlns.com/foaf/0.1/')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2003/06/sw-vocab-status/ns#'
                    'term_status'),
             Literal('testing')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#range'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#Literal')),
            (URIRef('http://xmlns.com/foaf/0.1/name'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#subPropertyOf'),
             URIRef('http://www.w3.org/2000/01/rdf-schema#label'))},
            name.triples)

        # Test `is_superclass_of` method.
        self.assertTrue(name.is_superclass_of(name))
        nick = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/nick'))
        self.assertTrue(isinstance(nick, OntologyAttribute))
        self.assertFalse(name.is_superclass_of(nick))

        # Test `ìs_subclass_of` method.
        self.assertTrue(name.is_subclass_of(name))
        self.assertFalse(name.is_subclass_of(nick))

        # Test `__eq__` method.
        self.assertEqual(name, name)
        self.assertNotEqual(name, nick)

        # Test `__hash__` method.
        self.assertTrue(isinstance(name, Hashable))

        # Test `datatype` property.
        self.assertEqual(
            name.datatype,
            URIRef('http://www.w3.org/2000/01/rdf-schema#Literal'))

        # Test `convert_to_datatype` method.
        self.assertEqual('a_name', name.convert_to_datatype('a_name'))

    def test_oclass(self):
        """Tests the OntologyClass subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        ontology = self.ontology

        # Test with foaf:Person class.
        person = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/Person'))
        self.assertTrue(isinstance(person, OntologyClass))

        # Test the `attributes` property.
        self.assertDictEqual(dict(), person.attributes)

        # Test the `axioms` property.
        self.assertSetEqual(set(), set(person.axioms))

        # Test the `attribute declaration` .
        expected = {
            ontology.from_identifier(
                URIRef(f'http://xmlns.com/foaf/0.1/{suffix}')): (None,
                                                                 False)
            for suffix in ('firstName', 'lastName', 'geekcode', 'plan',
                           'familyName', 'surname', 'myersBriggs',
                           'family_name', 'birthday', 'jabberID',
                           'yahooChatID', 'gender', 'msnChatID',
                           'mbox_sha1sum', 'aimChatID', 'skypeID',
                           'status', 'age', 'icqChatID')}
        self.assertDictEqual(expected, person.attribute_declaration)

        # Test `__call__` method.
        # self.assertTrue(isinstance(person(), OntologyIndividual))

    def test_relationship(self):
        """Tests the OntologyRelationship subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        ontology = self.ontology

        # Test with foaf:member class.
        member = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/member'))
        self.assertTrue(isinstance(member, OntologyRelationship))

    def test_annotation(self):
        """Tests the OntologyAnnotation subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        ontology = self.ontology

        # Test with foaf:membershipClass annotation property.
        membership_class = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/membershipClass'))
        self.assertTrue(isinstance(membership_class, OntologyAnnotation))

    def test_oclass_composition(self):
        """Tests the Compsition subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        # We do nothing, as the FOAF ontology has no compositions.
        pass

    def test_oclass_restriction(self):
        """Tests the OntologyClass subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        # We do nothing, as the FOAF ontology has no axioms.
        pass

    def test_namespace(self):
        """Tests the OntologyNamespace class."""
        ontology = self.ontology

        # Get the namespace from the ontology.
        foaf_namespace = ontology.get_namespace('foaf')
        self.assertTrue(isinstance(foaf_namespace, OntologyNamespace))

        # Test the `name` property.
        self.assertEqual(foaf_namespace.name, 'foaf')

        # Test the `iri` property.
        self.assertEqual(foaf_namespace.iri,
                         URIRef('http://xmlns.com/foaf/0.1/'))

        # Test the `__eq__` method.
        self.assertEqual(ontology.get_namespace('foaf'),
                         foaf_namespace)

        # Test the `__getattr__` method.
        member = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/member'))
        self.assertEqual(member, getattr(foaf_namespace, 'member'))

        # Test the `__getitem__` method.
        name = ontology.from_identifier(
            URIRef('http://xmlns.com/foaf/0.1/name'))
        self.assertFalse(foaf_namespace.reference_style)
        self.assertEqual(name, foaf_namespace['name'])

        # Test the `__dir__` method.
        self.assertIn('birthday', dir(foaf_namespace))

        # Test the `__iter__` method.
        self.assertEqual(162, len(tuple(foaf_namespace)))
        self.assertIn(name, tuple(foaf_namespace))
        self.assertIn(member, tuple(foaf_namespace))

        # Test the `__contains__` method.
        self.assertIn(name, foaf_namespace)
        self.assertIn(member, foaf_namespace)
        self.assertIn(name.iri, foaf_namespace)
        self.assertIn(member.iri, foaf_namespace)
        self.assertNotIn(URIRef('other:some_iri'), foaf_namespace)

    def test_individual(self):
        """Tests the OntologyIndividual subclass.

        DOES include methods inherited from OntologyEntity.
        """
        ontology = self.ontology
        from osp.core.namespaces import foaf

        # Test the `__init__` method by creating a new individual.
        person = foaf.Person(session=ontology)

        # Test the class related methods `oclass`, `oclasses`, `is_a`.
        self.assertTrue(isinstance(person,
                                   OntologyIndividual))
        self.assertEqual(person.oclass, foaf.Person)
        self.assertSetEqual(set(person.oclasses), {foaf.Person})
        self.assertTrue(person.is_a(foaf.Person))
        self.assertFalse(person.is_a(foaf.Organization))
        self.assertTrue(person.is_a(foaf.Agent))

        # Test the `__dir__` method.
        self.assertTrue('age' in dir(person))

        # Test the `__getattr__` and `__setattr__` methods.
        self.assertIsNone(person.age)
        person.age = '25'
        self.assertEqual(person.age, '25')

        # Test the `__getitem__`, `__setitem__` and `__delitem__` methods.
        self.assertEqual(person[foaf.age], '25')
        del person[foaf.age]
        self.assertIsNone(person.age)
        person[foaf.age, :] = {'26'}
        self.assertEqual(person[foaf.age], '26')
        self.assertSetEqual(person[foaf.age, :], {'26'})
        person[foaf.age, :] += '57'
        self.assertSetEqual(person[foaf.age, :], {'26', '57'})
        person[foaf.age, :] -= '26'
        self.assertSetEqual(person[foaf.age, :], {'57'})
        del person[foaf.age]
        self.assertIsNone(person.age)

        # Test subscripting notation for ontology individuals.
        another_person = foaf.Person(session=ontology)
        one_more_person = foaf.Person(session=ontology)
        person[foaf.knows] = another_person
        self.assertEqual(person[foaf.knows], another_person)
        person[foaf.knows, :] += {one_more_person}
        self.assertSetEqual(person[foaf.knows, :], {another_person,
                                                    one_more_person})
        person[foaf.knows, :] -= {another_person}
        self.assertSetEqual(person[foaf.knows, :], {one_more_person})
        person[foaf.knows, :].clear()
        self.assertSetEqual(person[foaf.knows, :], set())

        # Test annotation of ontology individuals.
        group = foaf.Group()
        group[foaf.member, :] = {person, another_person, one_more_person}
        group[foaf.membershipClass] = foaf.Person
        self.assertSetEqual({foaf.Person},
                            group[foaf.membershipClass, :])
        group[foaf.membershipClass, :] += 18
        group[foaf.membershipClass, :] += 'a string'
        group[foaf.membershipClass, :] += group
        self.assertSetEqual({foaf.Person, 18, 'a string', group},
                            group[foaf.membershipClass, :])
        group[foaf.membershipClass, :] = Literal('15', datatype=XSD.decimal)
        self.assertEqual(Decimal,
                         type(group[foaf.membershipClass]))


class TestLoadParsers(unittest.TestCase):
    """Test merging ontology packages in the ontology."""

    def setUp(self) -> None:
        """Set up ontology."""
        self.ontology = Session(identifier='some_ontology',
                                ontology=True)

    def test_loading_packages(self):
        """Test merging several ontology packages."""
        parsers = (
            OWLParser('foaf'),
            OWLParser('emmo'),
            OWLParser('dcat2'),
            YMLParser('city')
        )
        for parser in parsers:
            self.ontology.load_parser(parser)

        # Test that all namespaces were loaded.
        city_namespaces = {'city': "http://www.osp-core.com/city#"}
        foaf_namespaces = {'foaf': "http://xmlns.com/foaf/0.1/"}
        dcat2_namespaces = {'dcat2': "http://www.w3.org/ns/dcat#"}
        emmo_namespaces = {
            'annotations': 'http://emmo.info/emmo/top/annotations#',
            'holistic': "http://emmo.info/emmo/middle/holistic#",
            'isq': "http://emmo.info/emmo/middle/isq#",
            'manufacturing': "http://emmo.info/emmo/middle/manufacturing#",
            'materials': "http://emmo.info/emmo/middle/materials#",
            'math': "http://emmo.info/emmo/middle/math#",
            'meretopology': "http://emmo.info/emmo/top/mereotopology#",
            'metrology': "http://emmo.info/emmo/middle/metrology#",
            'models': "http://emmo.info/emmo/middle/models#",
            'perceptual': "http://emmo.info/emmo/middle/perceptual#",
            'physical': "http://emmo.info/emmo/top/physical#",
            'physicalistic': "http://emmo.info/emmo/middle/physicalistic#",
            'properties': "http://emmo.info/emmo/middle/properties#",
            'reductionistic': "http://emmo.info/emmo/middle/reductionistic#",
            'semiotics': "http://emmo.info/emmo/middle/semiotics#",
            'siunits': "http://emmo.info/emmo/middle/siunits#",
            'top': "http://emmo.info/emmo/top#",
        }
        expected_namespaces = dict()
        for nss in (foaf_namespaces, dcat2_namespaces,
                    emmo_namespaces, city_namespaces):
            expected_namespaces.update(nss)
        self.assertSetEqual(
            set(OntologyNamespace(iri=iri,
                                  name=name,
                                  ontology=self.ontology)
                for name, iri in expected_namespaces.items()),
            set(self.ontology.namespaces)
        )

        # Check that names of the namespaces were loaded.
        self.assertSetEqual(
            set(expected_namespaces.keys()),
            set(ns.name for ns in self.ontology.namespaces)
        )

        # Check that the default relationships were properly loaded.
        expected_default_relationships = {
            OntologyNamespace(iri=iri,
                              name=name,
                              ontology=self.ontology):
            OntologyRelationship(
                uid=UID("http://emmo.info/emmo/top/mereotopology#"
                        "EMMO_17e27c22_37e1_468c_9dd7_95e137f73e7f"),
                session=self.ontology)
            for name, iri in emmo_namespaces.items()
        }
        expected_default_relationships.update(
            {OntologyNamespace(iri="http://www.osp-core.com/city#",
                               name="city",
                               ontology=self.ontology):
             OntologyRelationship(
                 uid=UID("http://www.osp-core.com/city#hasPart"),
                 session=self.ontology)}
        )
        self.assertDictEqual(
            expected_default_relationships,
            self.ontology.default_relationships
        )

        # Check that the active relationships were properly loaded.
        self.assertSetEqual(
            {OntologyRelationship(
                uid=UID("http://emmo.info/emmo/top/mereotopology#"
                        "EMMO_8c898653_1118_4682_9bbf_6cc334d16a99"),
                session=self.ontology),
             OntologyRelationship(
                uid=UID("http://emmo.info/emmo/middle/semiotics#"
                        "EMMO_60577dea_9019_4537_ac41_80b0fb563d41"),
                session=self.ontology),
             OntologyRelationship(
                uid=UID("http://www.osp-core.com/city#encloses"),
                session=self.ontology)},
            set(self.ontology.active_relationships)
        )

        # Check that the reference styles were properly loaded.
        self.assertDictEqual(
            {OntologyNamespace(iri=iri, name=name, ontology=self.ontology):
                True if name in emmo_namespaces else False
             for name, iri in expected_namespaces.items()},
            self.ontology.reference_styles,
        )

        # Try to fetch all the namespaces by name.
        self.assertSetEqual(
            set(self.ontology.namespaces),
            set(self.ontology.get_namespace(name)
                for name in expected_namespaces),
        )


if __name__ == "__main__":
    unittest.main()