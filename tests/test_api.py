"""Test all public API methods.

The public API methods are the methods that are available to the users,
and available in the user documentation.
"""

import tempfile
import unittest
from decimal import Decimal
from typing import Hashable

from rdflib import RDFS, XSD, Graph, Literal, URIRef

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.tools import sparql
from simphony_osp.utils.datatypes import UID


class TestSession(unittest.TestCase):
    """Tests the session class public methods."""

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser("city"))
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
        has_inhabitant = ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#hasInhabitant")
        )
        self.assertTrue(isinstance(has_inhabitant, OntologyRelationship))
        encloses = ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#encloses")
        )
        self.assertTrue(isinstance(encloses, OntologyRelationship))
        has_part = ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#hasPart")
        )
        self.assertTrue(isinstance(has_part, OntologyRelationship))
        name = ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#name")
        )
        self.assertTrue(isinstance(name, OntologyAttribute))

        # Test `active_relationships property`.
        self.assertIn(encloses, ontology.active_relationships)
        ontology.active_relationships = (has_inhabitant,)
        self.assertIn(has_inhabitant, ontology.active_relationships)
        self.assertNotIn(encloses, ontology.active_relationships)
        ontology.active_relationships = (encloses, has_inhabitant)
        self.assertIn(encloses, ontology.active_relationships)
        self.assertIn(has_inhabitant, ontology.active_relationships)
        ontology.active_relationships = (encloses,)

        # Test the `get_namespace` method.
        self.assertRaises(KeyError, ontology.get_namespace, "fake")
        city_namespace = ontology.get_namespace("city")
        self.assertTrue(isinstance(city_namespace, OntologyNamespace))
        self.assertEqual(city_namespace.name, "city")
        self.assertEqual(
            city_namespace.iri, URIRef("https://www.simphony-project.eu/city#")
        )

        # Test `default_relationship` property.
        original_default_relationships = ontology.default_relationships
        self.assertIn(has_part, ontology.default_relationships.values())
        ontology.default_relationships = {city_namespace: has_inhabitant}
        self.assertIn(has_inhabitant, ontology.default_relationships.values())
        ontology.default_relationships = None
        self.assertDictEqual(ontology.default_relationships, dict())
        ontology.default_relationships = original_default_relationships
        self.assertIn(has_part, ontology.default_relationships.values())

        # Test `reference_styles` property.
        self.assertFalse(ontology.reference_styles[city_namespace])
        ontology.reference_styles = {city_namespace: True}
        self.assertTrue(ontology.reference_styles[city_namespace])
        ontology.reference_styles = {city_namespace: False}
        self.assertFalse(ontology.reference_styles[city_namespace])

        # Test the `graph` property.
        self.assertTrue(isinstance(ontology.graph, Graph))

    def test_sparql(self):
        """Test SPARQL by creating a city and performing a very simple query.

        Create a city with a single inhabitant and perform a very simple SPARQL
        query using both the `sparql` function from utils and the sparql method
        of the session.
        """
        # Clear the default session's contents.
        Session.get_default_session().clear()

        from simphony_osp.namespaces import city

        def is_freiburg(iri):
            value = str(iri)
            if value == "Freiburg":
                return True
            else:
                return False

        freiburg = city.City(name="Freiburg", coordinates=[0, 0])
        karl = city.Citizen(name="Karl", age=47)
        freiburg.add(karl, rel=city.hasInhabitant)
        default_session = freiburg.session
        query = f"""SELECT ?city_name ?citizen ?citizen_age ?citizen_name
                    WHERE {{ ?city a <{city.City.iri}> .
                             ?city <{city['name'].iri}> ?city_name .
                             ?city <{city.hasInhabitant.iri}> ?citizen .
                             ?citizen <{city['name'].iri}> ?citizen_name .
                             ?citizen <{city.age.iri}> ?citizen_age .
                          }}
                 """
        datatypes = dict(
            citizen=OntologyIndividual,
            citizen_age=int,
            citizen_name=str,
            city_name=is_freiburg,
        )
        results_none = sparql(query, session=None)
        results_default_session = sparql(query, session=default_session)
        results_default_session_method = default_session.sparql(query)
        self.assertEqual(len(results_none), 1)
        self.assertEqual(len(results_default_session), 1)
        self.assertEqual(len(results_default_session_method), 1)

        results = (
            next(results_none(**datatypes)),
            next(results_default_session(**datatypes)),
            next(results_default_session_method(**datatypes)),
        )
        self.assertTrue(
            all(result["citizen"].is_a(karl.oclass) for result in results)
        )
        self.assertTrue(
            all(result["citizen_age"] == karl.age for result in results)
        )
        self.assertTrue(
            all(result["citizen_name"] == karl.name for result in results)
        )
        self.assertTrue(all(result["city_name"] for result in results))

        results = (
            next(iter(results_none)),
            next(iter(results_default_session)),
            next(iter(results_default_session_method)),
        )
        self.assertTrue(
            all(result["citizen"] == karl.iri for result in results)
        )
        self.assertTrue(
            all(type(result["citizen_age"]) != int for result in results)
        )


class TestOntologyEntityCity(unittest.TestCase):
    """Test the ontology API using the city ontology."""

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def test_attribute(self):
        """Tests the OntologyAttribute subclass.

        Includes methods inherited from OntologyEntity.
        """
        from simphony_osp.namespaces import city, owl

        # Test with city:name attribute.
        name = city["name"]
        age = city.age
        number = city.number
        self.assertTrue(isinstance(name, OntologyAttribute))

        # Test `uid` property.
        self.assertEqual(
            name.uid, UID(URIRef("https://www.simphony-project.eu/city#name"))
        )
        name.uid = UID(
            URIRef("https://www.simphony-project.eu/city#other_name")
        )
        self.assertEqual(
            name.uid,
            UID(URIRef("https://www.simphony-project.eu/city#other_name")),
        )
        name.uid = UID(URIRef("https://www.simphony-project.eu/city#name"))

        # Test `identifier property`.
        self.assertEqual(
            name.identifier,
            URIRef("https://www.simphony-project.eu/city#name"),
        )

        # Test `iri` property.
        self.assertEqual(
            name.iri, URIRef("https://www.simphony-project.eu/city#name")
        )

        # Test `label` property.
        self.assertEqual(str, type(name.label))
        self.assertEqual("name", name.label)

        # Test `label_lang` property.
        self.assertEqual("en", name.label_lang)

        # Test 'label_literal' property.
        self.assertEqual(Literal("name", lang="en"), name.label_literal)

        # Test `iter_labels` method.
        # Test `lang = None`, `return_prop = False`, `return_literal = True`.
        self.assertTupleEqual(
            (Literal("name", lang="en"),), tuple(name.iter_labels())
        )
        # Test `lang = "en"`, `return_prop = False`, `return_literal = True`.
        self.assertTupleEqual(
            (Literal("name", lang="en"),), tuple(name.iter_labels(lang="en"))
        )
        # Test `lang = None`, `return_prop = True`, `return_literal = True`.
        self.assertTupleEqual(
            ((Literal("name", lang="en"), URIRef(RDFS.label)),),
            tuple(name.iter_labels(return_prop=True)),
        )
        # Test `lang = None`, `return_prop = True`, `return_literal = False`.
        self.assertTupleEqual(
            (("name", URIRef(RDFS.label)),),
            tuple(name.iter_labels(return_literal=False, return_prop=True)),
        )
        # Test `lang = None`, `return_prop = False`, `return_literal = False`.
        self.assertTupleEqual(
            ("name",),
            tuple(name.iter_labels(return_literal=False, return_prop=False)),
        )

        # Test `session` property.
        self.assertIs(name.session, self.ontology)
        # TODO: Test setter.

        # Test `direct_superclasses` property.
        self.assertSetEqual(set(), name.direct_superclasses)

        # Test `direct_subclasses` property.
        self.assertSetEqual(set(), name.direct_subclasses)

        # Test `superclasses` property.
        self.assertSetEqual({name, owl.topDataProperty}, name.superclasses)

        # Test `subclasses` property.
        self.assertSetEqual({name}, name.subclasses)

        # Test `triples` property.
        self.assertSetEqual(
            {
                (
                    URIRef("https://www.simphony-project.eu/city#name"),
                    URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                    URIRef("http://www.w3.org/2002/07/owl#DatatypeProperty"),
                ),
                (
                    URIRef("https://www.simphony-project.eu/city#name"),
                    URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                    URIRef("http://www.w3.org/2002/07/owl#FunctionalProperty"),
                ),
                (
                    URIRef("https://www.simphony-project.eu/city#name"),
                    URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                    Literal("name", lang="en"),
                ),
                (
                    URIRef("https://www.simphony-project.eu/city#name"),
                    URIRef("http://www.w3.org/2000/01/rdf-schema#range"),
                    URIRef("http://www.w3.org/2001/XMLSchema#string"),
                ),
            },
            name.triples,
        )

        # Test `is_superclass_of` method.
        self.assertTrue(age.is_superclass_of(age))
        self.assertTrue(isinstance(number, OntologyAttribute))
        self.assertTrue(number.is_superclass_of(age))
        self.assertFalse(age.is_superclass_of(number))

        # Test `ìs_subclass_of` method.
        self.assertTrue(number.is_subclass_of(number))
        self.assertTrue(age.is_subclass_of(number))
        self.assertFalse(number.is_subclass_of(age))

        # Test `__eq__` method.
        self.assertEqual(age, age)
        self.assertNotEqual(name, number)

        # Test `__hash__` method.
        self.assertTrue(isinstance(number, Hashable))

        # Test `datatype` property.
        self.assertEqual(XSD.string, name.datatype)
        self.assertEqual(
            city.age.datatype,
            URIRef("http://www.w3.org/2001/XMLSchema#integer"),
        )

        # Test `convert_to_datatype` method.
        self.assertEqual(5, city.age.convert_to_datatype("5"))

    def test_oclass(self):
        """Tests the OntologyClass subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        from simphony_osp.namespaces import city

        # Test with city:Person class.
        person = city.Person
        self.assertTrue(isinstance(person, OntologyClass))

        # Test the `attributes` property.
        self.assertDictEqual(dict(), person.attributes)

        # Test the `axioms` property.
        self.assertEqual(4, len(person.axioms))

        # Test the `attribute declaration` .
        expected = {city["name"]: (None, True), city.age: (None, True)}
        print(person.attribute_declaration)
        self.assertDictEqual(expected, person.attribute_declaration)

        # Test `__call__` method.
        # self.assertTrue(isinstance(person(), OntologyIndividual))

    def test_oclass_composition(self):
        """Tests the Compsition subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        # TODO
        pass

    def test_oclass_restriction(self):
        """Tests the OntologyClass subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        # TODO
        pass

    def test_relationship(self):
        """Tests the OntologyRelationship subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        # Test with city:hasWorker relationship.
        has_worker = self.ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#hasWorker")
        )
        self.assertTrue(isinstance(has_worker, OntologyRelationship))

    def test_namespace(self):
        """Tests the OntologyNamespace class."""
        ontology = self.ontology

        # Get the namespace from the ontology.
        city_namespace = ontology.get_namespace("city")
        self.assertTrue(isinstance(city_namespace, OntologyNamespace))

        # Test the `name` property.
        self.assertEqual(city_namespace.name, "city")

        # Test the `iri` property.
        self.assertEqual(
            city_namespace.iri, URIRef("https://www.simphony-project.eu/city#")
        )

        # Test the `__eq__` method.
        self.assertEqual(ontology.get_namespace("city"), city_namespace)

        # Test the `__getattr__` method.
        has_inhabitant = ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#hasInhabitant")
        )
        self.assertEqual(
            has_inhabitant, getattr(city_namespace, "hasInhabitant")
        )

        # Test the `__getitem__` method.
        name = ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#name")
        )
        self.assertFalse(city_namespace.reference_style)
        self.assertEqual(name, city_namespace["name"])

        # Test the `__dir__` method.
        self.assertIn("hasMajor", dir(city_namespace))

        # Test the `__iter__` method.
        self.assertEqual(28, len(tuple(city_namespace)))
        self.assertIn(name, tuple(city_namespace))
        self.assertIn(has_inhabitant, tuple(city_namespace))

        # Test the `__contains__` method.
        self.assertIn(name, city_namespace)
        self.assertIn(has_inhabitant, city_namespace)
        self.assertIn(name.iri, city_namespace)
        self.assertIn(has_inhabitant.iri, city_namespace)
        self.assertNotIn(URIRef("other:some_iri"), city_namespace)

    def test_individual(self):
        """Tests the OntologyIndividual subclass.

        DOES include methods inherited from OntologyEntity.
        """
        from simphony_osp.namespaces import city, owl

        # Test the `__init__` method by creating new individuals.
        freiburg = city.City(name="Freiburg", coordinates=[0, 0])
        paris = city.City(name="Paris", coordinates=[0, 0])
        altstadt = city.Neighborhood(name="Altstadt", coordinates=[0, 0])
        dreherstrasse = city.Street(name="Dreherstraße", coordinates=[0, 0])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        self.assertRaises(
            TypeError,
            city.City,
            name="name",
            coordinates=[1, 2],
            uid=0,
            unwanted="unwanted",
        )
        self.assertRaises(TypeError, city.City)
        self.assertRaises(
            TypeError, OntologyIndividual, oclass=None, attributes={}
        )

        # Test the class related methods `oclass`, `oclasses`, `is_a`.
        self.assertTrue(isinstance(marc, OntologyIndividual))
        self.assertEqual(marc.oclass, city.Citizen)
        self.assertSetEqual(set(marc.oclasses), {city.Citizen})
        self.assertTrue(marc.is_a(city.Citizen))
        self.assertTrue(marc.is_a(city.LivingBeing))
        self.assertTrue(marc.is_a(city.Person))
        self.assertFalse(marc.is_a(city.City))

        # Test the `__dir__` method.
        self.assertTrue("age" in dir(marc))

        # Test the `__getattr__` and `__setattr__` methods.
        self.assertEqual(25, marc.age)
        marc.age = "30"
        self.assertEqual(marc.age, 30)
        marc.age = 25

        # Test the `__getitem__`, `__setitem__` and `__delitem__` methods.
        self.assertEqual(marc[city.age].one(), 25)
        del marc[city.age]
        self.assertIsNone(marc.age)
        marc[city.age] = {"26"}
        self.assertEqual(marc[city.age].one(), 26)
        self.assertSetEqual(marc[city.age], {26})
        marc[city.age] += "57"
        self.assertSetEqual(marc[city.age], {26, 57})
        marc[city.age] -= 26
        self.assertSetEqual(marc[city.age], {57})
        del marc[city.age]
        self.assertIsNone(marc.age)
        marc[city.age] = 25

        # Test subscripting notation for ontology individuals.
        freiburg[city.hasInhabitant] = marc
        self.assertEqual(freiburg[city.hasInhabitant].one(), marc)
        freiburg[city.hasInhabitant] += {sveta}
        self.assertSetEqual(freiburg[city.hasInhabitant], {marc, sveta})
        freiburg[city.hasInhabitant] -= {marc}
        self.assertSetEqual(freiburg[city.hasInhabitant], {sveta})
        freiburg[city.hasInhabitant].clear()
        self.assertSetEqual(freiburg[city.hasInhabitant], set())

        # Test `add` method of ontology individuals.
        self.assertRaises(TypeError, freiburg.add, "a string")
        freiburg.add(altstadt)
        self.assertEqual(freiburg.get(altstadt.uid).uid, altstadt.uid)
        # get_inverse = n.get(rel=city.isPartOf)
        # self.assertSetEqual(get_inverse, {c})
        altstadt.add(dreherstrasse)
        freiburg.add(marc, rel=city.hasInhabitant)
        freiburg.add(sveta, rel=city.hasInhabitant.identifier)
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        self.assertSetEqual({dreherstrasse}, altstadt[city.hasPart])
        freiburg.add(paris, rel=owl.topObjectProperty)
        f1 = paris.add(freiburg, rel=owl.topObjectProperty)
        f2 = paris.add(freiburg, rel=owl.topObjectProperty)
        self.assertEqual(f1, f2)
        # Test containment behavior.
        another_session = Session(ontology=self.ontology)
        another_session.update(freiburg)
        new_freiburg = another_session.from_identifier(freiburg.identifier)
        self.assertIs(new_freiburg.session, another_session)
        self.assertIsNot(freiburg.session, another_session)
        self.assertIsNot(freiburg[city.hasInhabitant].any(), another_session)
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        self.assertNotIn(marc, new_freiburg[city.hasInhabitant])
        self.assertNotIn(sveta, new_freiburg[city.hasInhabitant])
        new_marc = another_session.from_identifier(marc.identifier)
        new_sveta = another_session.from_identifier(sveta.identifier)
        self.assertSetEqual(
            {new_marc, new_sveta}, new_freiburg[city.hasInhabitant]
        )
        self.assertSetEqual(set(), marc[city.hasChild])
        child_1 = city.Citizen(name="Baby 1", age=2)
        child_2 = city.Citizen(name="Baby 2", age=2, session=another_session)
        marc[city.hasChild] = child_1
        new_marc[city.hasChild] = child_2
        self.assertSetEqual({child_1}, marc[city.hasChild])
        self.assertSetEqual({child_2}, new_marc[city.hasChild])

        # Test `get` method of ontology individuals.
        self.assertRaises(TypeError, freiburg.get, "not an UID")
        self.assertRaises(
            ValueError, freiburg.get, sveta.uid, oclass=city.Neighborhood
        )
        self.assertRaises(TypeError, freiburg.get, oclass=city.hasInhabitant)
        self.assertRaises(TypeError, freiburg.get, rel=city.Citizen)
        # get()
        self.assertSetEqual({marc, sveta, altstadt}, freiburg.get())
        # get(*uids)
        self.assertEqual(marc, freiburg.get(marc.uid))
        self.assertEqual(sveta, freiburg.get(sveta.uid))
        self.assertTupleEqual((sveta, marc), freiburg.get(sveta.uid, marc.uid))
        self.assertIsNone(freiburg.get(UID()))
        # get(rel=___)
        self.assertSetEqual(
            {marc, sveta}, freiburg.get(rel=city.hasInhabitant)
        )
        self.assertSetEqual(
            {marc, sveta, altstadt}, freiburg.get(rel=city.encloses)
        )
        # get(oclass=___)
        self.assertSetEqual({marc, sveta}, freiburg.get(oclass=city.Citizen))
        self.assertSetEqual(set(), freiburg.get(oclass=city.Building))
        self.assertSetEqual({sveta, marc}, freiburg.get(oclass=city.Person))
        self.assertSetEqual(
            set(), freiburg.get(oclass=city.ArchitecturalStructure)
        )
        # get(*uids, rel=___)
        self.assertEqual(marc, freiburg.get(marc.uid, rel=city.hasInhabitant))
        self.assertIsNone(freiburg.get(marc.uid, rel=city.hasPart))
        # get(rel=___, oclass=___)
        self.assertSetEqual(
            {marc, sveta},
            freiburg.get(rel=city.hasInhabitant, oclass=city.Citizen),
        )
        # return_rel=True
        get_marc, get_marc_rel = freiburg.get(marc.uid, return_rel=True)
        self.assertEqual(get_marc, marc)
        self.assertEqual(get_marc_rel, city.hasInhabitant)
        self.assertSetEqual(
            {
                (marc, city.hasInhabitant),
                (sveta, city.hasInhabitant),
                (altstadt, city.hasPart),
            },
            set(freiburg.get(rel=city.encloses, return_rel=True)),
        )

        # Test `iter` method of ontology individuals.
        self.assertSetEqual({marc, sveta, altstadt}, set(freiburg.iter()))
        # return_rel=True
        get_marc, get_marc_rel = next(freiburg.iter(marc.uid, return_rel=True))
        self.assertEqual(get_marc, marc)
        self.assertEqual(get_marc_rel, city.hasInhabitant)
        self.assertSetEqual(
            {
                (marc, city.hasInhabitant),
                (sveta, city.hasInhabitant),
                (altstadt, city.hasPart),
            },
            set(freiburg.iter(rel=city.encloses, return_rel=True)),
        )

        # Test `update` method of ontology individuals.
        session = Session(ontology=self.ontology)
        napoli = city.City(name="Napoli", coordinates=[0, 0])
        neighborhood = city.Neighborhood(
            name="Quartieri Spagnoli", coordinates=[0, 0]
        )
        session.update(neighborhood)
        new_neighborhood = session.from_identifier(neighborhood.identifier)
        new_street = city.Street(
            name="Via Concordia", coordinates=[0, 0], session=session
        )
        new_neighborhood.add(new_street)
        napoli.add(neighborhood)
        self.assertSetEqual(set(), neighborhood.get(oclass=city.Street))
        napoli.update(new_neighborhood)
        street = napoli.session.from_identifier(new_street.identifier)
        self.assertSetEqual({street}, neighborhood.get(oclass=city.Street))
        self.assertRaises(ValueError, napoli.update, neighborhood)
        other_neighborgood = city.Neighborhood(
            name="Vasto", coordinates=[0, 0]
        )
        self.assertRaises(ValueError, napoli.update, other_neighborgood)

        # Test `remove` method of ontology individuals.
        self.assertRaises(TypeError, freiburg.remove, "a string")
        self.assertRaises(
            ValueError, freiburg.remove, altstadt.uid, oclass=city.Street
        )
        # remove()
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.remove()
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        # remove(*uids_or_individuals)
        freiburg[city.hasInhabitant] = {marc, sveta}
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.remove(marc.uid)
        self.assertSetEqual({sveta}, freiburg[city.hasInhabitant])
        freiburg.remove(sveta)
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        freiburg[city.hasInhabitant] = {marc, sveta}
        # remove(rel=___)
        freiburg[city.hasInhabitant] = {marc, sveta}
        freiburg[city.hasPart] = {altstadt}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.remove(rel=city.hasPart)
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        self.assertSetEqual(set(), freiburg[city.hasPart])
        # remove(oclass=___)
        freiburg[city.hasPart] = {altstadt}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.remove(oclass=city.Citizen)
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        # remove(*uids_or_individuals, rel=___)
        freiburg[city.hasInhabitant] = {marc, sveta}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.remove(marc, sveta, rel=city.hasInhabitant)
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        # remove(rel=___, oclass=___)
        freiburg[city.hasInhabitant] = {marc, sveta}
        freiburg[city.hasInhabitant] += {altstadt}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual(
            {marc, sveta, altstadt}, freiburg[city.hasInhabitant]
        )
        freiburg.remove(rel=city.hasInhabitant, oclass=city.Citizen)
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({altstadt}, freiburg[city.hasInhabitant])

        # Test `attributes_get` method of individuals.
        self.assertDictEqual(
            marc.attributes_get(), {city["name"]: {"Marc"}, city.age: {25}}
        )

    def test_multi_session(self):
        """Test several methods within a session context manager."""
        from simphony_osp.namespaces import city

        with Session() as session:
            freiburg = city.City(
                name="Freiburg", coordinates=[0, 0], session=session
            )
            marc_city = city.Citizen(name="Marc", age=25, session=session)
            sveta = city.Citizen(name="Sveta", age=25)
            mario = city.Citizen(name="Mario", age=25)
            sveta_city = marc_city.add(sveta)
            mario.add(sveta)
            freiburg.add(mario)
            self.assertIn(sveta_city, marc_city.get())

    def test_bracket_notation(self):
        """Detailed test of the functionality of the bracket notation."""
        from simphony_osp.namespaces import city

        paris = city.City(name="Paris", coordinates=[0, 0])
        marc = city.Citizen(name="Marc", age=25)
        aimee = city.Citizen(name="Aimée", age=25)
        clement = city.Citizen(name="Clément", age=25)

        # --- Test relationships ---

        # Basic functionality, assignment using single elements.
        self.assertSetEqual(set(), paris[city.hasMajor])
        paris[city.hasMajor] = marc
        self.assertSetEqual({marc}, paris[city.hasMajor])
        paris[city.hasMajor] = aimee
        self.assertSetEqual({aimee}, paris[city.hasMajor])
        paris[city.hasMajor] = None
        self.assertSetEqual(set(), paris[city.hasMajor])
        paris[city.hasMajor] = aimee
        del paris[city.hasMajor]
        self.assertSetEqual(set(), paris[city.hasMajor])
        self.assertRaises(
            TypeError, lambda x: paris.__setitem__(city.hasMajor, x), "String"
        )

        # Set features, assignment using sets.
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        self.assertSetEqual({marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] = set()
        self.assertEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        paris[city.hasInhabitant] = None
        self.assertEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        del paris[city.hasInhabitant]
        self.assertEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        paris[city.hasInhabitant].clear()
        self.assertEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        self.assertIn(marc, paris[city.hasInhabitant])
        self.assertNotIn(aimee, paris[city.hasInhabitant])
        self.assertSetEqual({marc}, set(paris[city.hasInhabitant]))
        self.assertEqual(1, len(paris[city.hasInhabitant]))
        self.assertLessEqual(paris[city.hasInhabitant], {marc})
        self.assertLessEqual(paris[city.hasInhabitant], {marc, aimee})
        self.assertFalse(paris[city.hasInhabitant] <= set())
        self.assertLess(paris[city.hasInhabitant], {marc, aimee})
        self.assertFalse(paris[city.hasInhabitant] < {marc})
        self.assertEqual({marc}, paris[city.hasInhabitant])
        self.assertNotEqual(paris[city.hasInhabitant], {marc, aimee})
        self.assertNotEqual(paris[city.hasInhabitant], set())
        self.assertGreater(paris[city.hasInhabitant], set())
        self.assertGreaterEqual(paris[city.hasInhabitant], set())
        self.assertGreaterEqual(paris[city.hasInhabitant], {marc})
        self.assertFalse(paris[city.hasInhabitant] >= {marc, aimee})
        self.assertSetEqual(set(), paris[city.hasInhabitant] & set())
        self.assertSetEqual({marc}, paris[city.hasInhabitant] & {marc})
        self.assertSetEqual(set(), paris[city.hasInhabitant] & {aimee})
        self.assertSetEqual({marc, aimee}, paris[city.hasInhabitant] | {aimee})
        self.assertSetEqual({marc}, paris[city.hasInhabitant] | {marc})
        self.assertSetEqual({marc}, paris[city.hasInhabitant] | set())
        self.assertSetEqual(set(), paris[city.hasInhabitant] - {marc})
        self.assertSetEqual({marc}, paris[city.hasInhabitant] - {aimee})
        self.assertSetEqual({marc, aimee}, paris[city.hasInhabitant] ^ {aimee})
        self.assertSetEqual(set(), paris[city.hasInhabitant] ^ {marc})
        self.assertTrue(paris[city.hasInhabitant].isdisjoint({aimee}))
        self.assertFalse(paris[city.hasInhabitant].isdisjoint({marc}))
        self.assertTrue(paris[city.hasInhabitant].isdisjoint(set()))
        self.assertEqual(marc, paris[city.hasInhabitant].pop())
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        self.assertIsNot(
            paris[city.hasInhabitant], paris[city.hasInhabitant].copy()
        )
        self.assertTrue(
            all(
                any(x == y for y in paris[city.hasInhabitant].copy())
                for x in paris[city.hasInhabitant]
            )
        )
        self.assertSetEqual(
            set(), paris[city.hasInhabitant].difference({marc})
        )
        self.assertSetEqual(
            {marc}, paris[city.hasInhabitant].difference({aimee})
        )
        paris[city.hasInhabitant].difference_update({aimee})
        self.assertSetEqual({marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant].difference_update({marc})
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        paris[city.hasInhabitant].discard(aimee)
        self.assertSetEqual({marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant].discard(marc)
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        self.assertSetEqual(
            {marc}, paris[city.hasInhabitant].intersection({marc})
        )
        self.assertSetEqual(
            set(), paris[city.hasInhabitant].intersection({aimee})
        )
        self.assertSetEqual(
            set(), paris[city.hasInhabitant].intersection(set())
        )
        paris[city.hasInhabitant].intersection_update({marc})
        self.assertSetEqual({marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant].intersection_update({aimee})
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {marc}
        paris[city.hasInhabitant].add(aimee)
        self.assertSetEqual({aimee, marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant].remove(aimee)
        self.assertSetEqual({marc}, paris[city.hasInhabitant])
        self.assertRaises(
            KeyError, lambda x: paris[city.hasInhabitant].remove(x), aimee
        )
        paris[city.hasInhabitant].update({aimee})
        self.assertSetEqual({aimee, marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] |= {aimee}
        self.assertSetEqual({aimee, marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {}
        paris[city.hasInhabitant] |= {aimee}
        self.assertSetEqual({aimee}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] &= {aimee}
        self.assertSetEqual({aimee}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] &= {marc}
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        paris[city.hasInhabitant] = {aimee}
        paris[city.hasInhabitant] ^= {marc}
        self.assertSetEqual({aimee, marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] ^= set()
        self.assertSetEqual({aimee, marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] ^= {aimee}
        self.assertSetEqual({marc}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] += {aimee}
        self.assertSetEqual({marc, aimee}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] -= {marc}
        self.assertSetEqual({aimee}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] += marc
        paris[city.hasInhabitant] += aimee
        self.assertSetEqual({marc, aimee}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] -= marc
        self.assertSetEqual({aimee}, paris[city.hasInhabitant])
        paris[city.hasInhabitant] -= aimee
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        self.assertRaises(
            TypeError,
            lambda x: paris.__setitem__(
                (city.hasInhabitant, slice(None, None, None)), x
            ),
            {"String"},
        )

        # Operations on sub-relationships.
        self.assertSetEqual(set(), paris[city.hasInhabitant])
        self.assertSetEqual(set(), paris[city.hasMajor])
        self.assertSetEqual(set(), paris[city.hasWorker])
        paris[city.hasMajor] += aimee
        paris[city.hasWorker] += marc
        paris[city.hasWorker] = {aimee, marc}  # Should not change hasMajor.
        paris[city.hasInhabitant] += clement
        self.assertSetEqual({aimee}, paris[city.hasMajor])
        self.assertSetEqual({aimee, marc}, paris[city.hasWorker])
        self.assertSetEqual({aimee, marc, clement}, paris[city.encloses])
        self.assertSetEqual({clement}, paris[city.hasInhabitant])
        paris[city.hasWorker] += {clement}
        self.assertSetEqual({aimee, marc, clement}, paris[city.hasWorker])
        self.assertSetEqual({aimee}, paris[city.hasMajor])
        paris[city.hasWorker] += {aimee}
        paris[city.hasMajor] -= {aimee}
        self.assertSetEqual({marc, clement}, paris[city.hasWorker])
        paris[city.hasWorker] += {aimee}
        self.assertSetEqual({marc, clement, aimee}, paris[city.hasWorker])
        paris[city.hasMajor] += {aimee}
        self.assertSetEqual({marc, clement, aimee}, paris[city.hasWorker])
        self.assertEqual(3, len(paris[city.hasWorker]))
        self.assertSetEqual({aimee}, paris[city.hasMajor])
        paris[city.hasMajor] -= {aimee}
        self.assertSetEqual({marc, clement, aimee}, paris[city.hasWorker])
        self.assertSetEqual(set(), paris[city.hasMajor])

        # Test attributes -> goto
        # TestOntologyEntityFOAF.test_bracket_notation.


class TestOntologyEntityFOAF(unittest.TestCase):
    """Test the ontology API using the FOAF ontology.

    Tests only features not tested with the City ontology.
    """

    # TODO: Extend the City ontology with annotation properties so that this
    #  test can be merged with `TestOntologyEntityCity`.

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and FOAF.
        """
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yml", delete=False
        ) as file:
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

        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser(yml_path))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def test_annotation(self):
        """Tests the OntologyAnnotation subclass.

        Does NOT include methods inherited from OntologyEntity.
        """
        ontology = self.ontology

        # Test with foaf:membershipClass annotation property.
        membership_class = ontology.from_identifier(
            URIRef("http://xmlns.com/foaf/0.1/membershipClass")
        )
        self.assertTrue(isinstance(membership_class, OntologyAnnotation))

    def test_individual(self):
        """Tests the OntologyIndividual subclass.

        DOES include methods inherited from OntologyEntity.
        """
        ontology = self.ontology
        from simphony_osp.namespaces import foaf

        # Test annotation of ontology individuals.
        group = foaf.Group()
        person = foaf.Person(session=ontology)
        another_person = foaf.Person(session=ontology)
        one_more_person = foaf.Person(session=ontology)
        group[foaf.member] = {person, another_person, one_more_person}
        group[foaf.membershipClass] = foaf.Person
        self.assertSetEqual({foaf.Person}, group[foaf.membershipClass])
        group[foaf.membershipClass] += 18
        group[foaf.membershipClass] += "a string"
        group[foaf.membershipClass] += group
        self.assertSetEqual(
            {foaf.Person, 18, "a string", group}, group[foaf.membershipClass]
        )
        group[foaf.membershipClass] = Literal("15", datatype=XSD.decimal)
        self.assertEqual(Decimal, type(group[foaf.membershipClass].any()))

    def test_bracket_notation(self):
        """Tests the functionality of the bracket notation.

        Only tests attributes, as all the relationships are tested on
        test_apy_city.TestAPICity.test_bracket_notation.
        """
        from simphony_osp.namespaces import foaf

        marc = foaf.Person()

        # --- Test attributes ---

        # Basic functionality, assignment using single elements.
        self.assertSetEqual(set(), marc[foaf["name"]])
        marc[foaf["name"]] = "Marc"
        self.assertSetEqual({"Marc"}, marc[foaf["name"]])
        marc[foaf["name"]] = "Marco"
        self.assertSetEqual({"Marco"}, marc[foaf["name"]])
        marc[foaf["name"]] = "Marc"
        del marc[foaf["name"]]
        self.assertSetEqual(set(), marc[foaf["name"]])
        marc[foaf["name"]] = "Marc"
        marc[foaf["name"]] = None
        self.assertSetEqual(set(), marc[foaf["name"]])
        marc[foaf["name"]] = "Marc"
        self.assertRaises(
            TypeError, lambda x: marc.__setitem__(foaf["name"], x), marc
        )

        # Set features, assignment using sets.
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        self.assertSetEqual({"Marc"}, marc[foaf.nick])
        marc[foaf.nick] = set()
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        marc[foaf.nick] = None
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        del marc[foaf.nick]
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        marc[foaf.nick].clear()
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        self.assertIn("Marc", marc[foaf.nick])
        self.assertNotIn("Aimee", marc[foaf.nick])
        self.assertSetEqual({"Marc"}, set(marc[foaf.nick]))
        self.assertEqual(1, len(marc[foaf.nick]))
        self.assertLessEqual(marc[foaf.nick], {"Marc"})
        self.assertLessEqual(marc[foaf.nick], {"Marc", "Aimee"})
        self.assertFalse(marc[foaf.nick] <= set())
        self.assertLess(marc[foaf.nick], {"Marc", "Aimee"})
        self.assertFalse(marc[foaf.nick] < {"Marc"})
        self.assertEqual({"Marc"}, marc[foaf.nick])
        self.assertNotEqual(marc[foaf.nick], {"Marc", "Aimee"})
        self.assertNotEqual(marc[foaf.nick], set())
        self.assertGreater(marc[foaf.nick], set())
        self.assertGreaterEqual(marc[foaf.nick], set())
        self.assertGreaterEqual(marc[foaf.nick], {"Marc"})
        self.assertFalse(marc[foaf.nick] >= {"Marc", "Aimee"})
        self.assertSetEqual(set(), marc[foaf.nick] & set())
        self.assertSetEqual({"Marc"}, marc[foaf.nick] & {"Marc"})
        self.assertSetEqual(set(), marc[foaf.nick] & {"Aimee"})
        self.assertSetEqual({"Marc", "Aimee"}, marc[foaf.nick] | {"Aimee"})
        self.assertSetEqual({"Marc"}, marc[foaf.nick] | {"Marc"})
        self.assertSetEqual({"Marc"}, marc[foaf.nick] | set())
        self.assertSetEqual(set(), marc[foaf.nick] - {"Marc"})
        self.assertSetEqual({"Marc"}, marc[foaf.nick] - {"Aimee"})
        self.assertSetEqual({"Marc", "Aimee"}, marc[foaf.nick] ^ {"Aimee"})
        self.assertSetEqual(set(), marc[foaf.nick] ^ {"Marc"})
        self.assertTrue(marc[foaf.nick].isdisjoint({"Aimee"}))
        self.assertFalse(marc[foaf.nick].isdisjoint({"Marc"}))
        self.assertTrue(marc[foaf.nick].isdisjoint(set()))
        self.assertEqual("Marc", marc[foaf.nick].pop())
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        self.assertIsNot(marc[foaf.nick], marc[foaf.nick].copy())
        self.assertSetEqual(marc[foaf.nick], marc[foaf.nick].copy())
        self.assertSetEqual(set(), marc[foaf.nick].difference({"Marc"}))
        self.assertSetEqual({"Marc"}, marc[foaf.nick].difference({"Aimee"}))
        marc[foaf.nick].difference_update({"Aimee"})
        self.assertSetEqual({"Marc"}, marc[foaf.nick])
        marc[foaf.nick].difference_update({"Marc"})
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        marc[foaf.nick].discard("Aimee")
        self.assertSetEqual({"Marc"}, marc[foaf.nick])
        marc[foaf.nick].discard("Marc")
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        self.assertSetEqual({"Marc"}, marc[foaf.nick].intersection({"Marc"}))
        self.assertSetEqual(set(), marc[foaf.nick].intersection({"Aimee"}))
        self.assertSetEqual(set(), marc[foaf.nick].intersection(set()))
        marc[foaf.nick].intersection_update({"Marc"})
        self.assertSetEqual({"Marc"}, marc[foaf.nick])
        marc[foaf.nick].intersection_update({"Aimee"})
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Marc"}
        marc[foaf.nick].add("Aimee")
        self.assertSetEqual({"Aimee", "Marc"}, marc[foaf.nick])
        marc[foaf.nick].remove("Aimee")
        self.assertSetEqual({"Marc"}, marc[foaf.nick])
        self.assertRaises(
            KeyError, lambda x: marc[foaf.nick].remove(x), "Aimee"
        )
        marc[foaf.nick].update({"Aimee"})
        self.assertSetEqual({"Aimee", "Marc"}, marc[foaf.nick])
        marc[foaf.nick] |= {"Aimee"}
        self.assertSetEqual({"Aimee", "Marc"}, marc[foaf.nick])
        marc[foaf.nick] = {}
        marc[foaf.nick] |= {"Aimee"}
        self.assertSetEqual({"Aimee"}, marc[foaf.nick])
        marc[foaf.nick] &= {"Aimee"}
        self.assertSetEqual({"Aimee"}, marc[foaf.nick])
        marc[foaf.nick] &= {marc}
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {"Aimee"}
        marc[foaf.nick] ^= {"Marc"}
        self.assertSetEqual({"Aimee", "Marc"}, marc[foaf.nick])
        marc[foaf.nick] ^= set()
        self.assertSetEqual({"Aimee", "Marc"}, marc[foaf.nick])
        marc[foaf.nick] ^= {"Aimee"}
        self.assertSetEqual({"Marc"}, marc[foaf.nick])
        marc[foaf.nick] += {"Aimee"}
        self.assertSetEqual({"Marc", "Aimee"}, marc[foaf.nick])
        marc[foaf.nick] -= {"Marc"}
        self.assertSetEqual({"Aimee"}, marc[foaf.nick])
        marc[foaf.nick] += "Marc"
        marc[foaf.nick] += "Aimee"
        self.assertSetEqual({"Marc", "Aimee"}, marc[foaf.nick])
        marc[foaf.nick] -= "Marc"
        self.assertSetEqual({"Aimee"}, marc[foaf.nick])
        marc[foaf.nick] -= "Aimee"
        self.assertSetEqual(set(), marc[foaf.nick])
        self.assertRaises(
            TypeError,
            lambda x: marc.__setitem__(
                (foaf.nick, slice(None, None, None)), x
            ),
            {marc},
        )

        # Operations on sub-attributes.
        self.assertSetEqual(set(), marc[foaf.nick])
        self.assertSetEqual(set(), marc[foaf.skypeID])
        marc[foaf.skypeID] += "marc_skype"
        marc[foaf.nick] += "marc_discord"
        marc[foaf.nick] = {
            "marc_skype",
            "marc_discord",
        }  # Should not change skypeID.
        self.assertSetEqual({"marc_skype"}, marc[foaf.skypeID])
        self.assertSetEqual({"marc_skype", "marc_discord"}, marc[foaf.nick])
        marc[foaf.nick] += "marc_skype"
        marc[foaf.skypeID] -= "marc_skype"
        self.assertSetEqual({"marc_discord"}, marc[foaf.nick])
        marc[foaf.nick] += "marc_skype"
        marc[foaf.skypeID] += "marc_skype"
        self.assertEqual(2, len(marc[foaf.nick]))
        self.assertSetEqual({"marc_skype"}, marc[foaf.skypeID])
        marc[foaf.skypeID] -= "marc_skype"
        self.assertSetEqual({"marc_skype", "marc_discord"}, marc[foaf.nick])
        self.assertSetEqual(set(), marc[foaf.skypeID])

        # Test relationships -> goto
        # test_api_city.TestAPICity.test_bracket_notation.


if __name__ == "__main__":
    unittest.main()


class TestContainer(unittest.TestCase):
    """Tests the containers."""

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        ontology = Session(identifier="test-tbox", ontology=True)
        ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def test_container(self):
        """Test the container ontology individual."""
        from simphony_osp.namespaces import city, cuba

        container = cuba.Container()

        self.assertIsNone(container.opens_in)
        self.assertIsNone(container.session_linked)
        self.assertFalse(container.is_open)
        self.assertSetEqual(set(), set(container.references))
        self.assertEqual(len(container.references), 0)
        self.assertEqual(container.num_references, 0)

        with container:
            self.assertIs(
                Session.get_default_session(), container.session_linked
            )
            self.assertTrue(container.is_open)
        self.assertIsNone(container.session_linked)
        self.assertFalse(container.is_open)

        self.assertEqual(len(container), 0)
        self.assertSetEqual(set(), set(container))

        session = Session()
        container.opens_in = session
        with container:
            self.assertTrue(container.is_open)
            self.assertIs(session, container.session_linked)
        self.assertIsNone(container.session_linked)
        self.assertFalse(container.is_open)
        self.assertRaises(
            TypeError, lambda x: setattr(container, "opens_in", x), 8
        )
        container.opens_in = None

        another_container = cuba.Container()

        another_container.opens_in = container
        self.assertRaises(RuntimeError, another_container.open)
        container.open()
        with another_container:
            self.assertIs(
                Session.get_default_session(), container.session_linked
            )
            self.assertIs(
                container.session_linked, another_container.session_linked
            )
        container.close()

        fr_session = Session()
        fr = city.City(name="Freiburg", coordinates=[0, 0], session=fr_session)
        container.references = {fr.iri}
        default_session = Session.get_default_session()

        self.assertIn(fr.iri, container.references)
        self.assertEqual(container.num_references, 1)
        with fr_session:
            with container:
                self.assertIs(fr_session, container.session_linked)
                self.assertIs(default_session, container.session)
                self.assertEqual(len(container), 1)
                self.assertSetEqual({fr}, set(container))
                self.assertIn(fr, container)

        broken_reference = URIRef("http://example.org/things#something")
        container.references = {broken_reference}
        self.assertIn(broken_reference, container.references)
        self.assertNotIn(fr, container)
        self.assertEqual(container.num_references, 1)
        with fr_session:
            self.assertEqual(len(container), 0)
            self.assertSetEqual(set(), set(container))
            self.assertNotIn(fr, container)

        container.connect(broken_reference)
        self.assertEqual(container.num_references, 1)
        container.connect(broken_reference)
        self.assertEqual(container.num_references, 1)
        container.disconnect(broken_reference)
        self.assertEqual(container.num_references, 0)

        with fr_session:
            container.add(fr)
            self.assertSetEqual({fr}, set(container))
            self.assertTrue(all(x.session is fr_session for x in container))
            container.remove(fr)
            self.assertEqual(container.num_references, 0)
            self.assertSetEqual(set(), set(container))
            container.add(fr)
            self.assertSetEqual({fr}, set(container))

        with container:
            self.assertEqual(container.num_references, 1)
            self.assertSetEqual(set(), set(container))

        with fr_session:
            with container:
                self.assertSetEqual({fr}, set(container))
                pr = city.City(name="Paris", coordinates=[0, 0])
                self.assertSetEqual({fr, pr}, set(container))

    def test_container_multiple_sessions(self):
        """Test opening the container in different sessions.

        Each session is meant to contain a different version of the same
        individual.
        """
        from simphony_osp.namespaces import city, cuba

        container = cuba.Container()

        default_session = Session.get_default_session()
        session_1 = Session()
        session_2 = Session()

        klaus = city.Citizen(name="Klaus", age=5)
        session_1.update(klaus)
        session_2.update(klaus)
        klaus_1 = session_1.from_identifier(klaus.identifier)
        klaus_1.age = 10
        klaus_2 = session_2.from_identifier(klaus.identifier)
        klaus_2.age = 20

        self.assertIs(klaus.session, default_session)
        self.assertIs(klaus_1.session, session_1)
        self.assertIs(klaus_2.session, session_2)
        self.assertEqual(klaus.age, 5)
        self.assertEqual(klaus_1.age, 10)
        self.assertEqual(klaus_2.age, 20)

        container.connect(klaus.identifier)

        with container:
            klaus_from_container = set(container).pop()
            self.assertEqual(klaus_from_container.age, 5)

        with session_1:
            with container:
                klaus_from_container = set(container).pop()
                self.assertEqual(klaus_from_container.age, 10)

        with session_2:
            with container:
                klaus_from_container = set(container).pop()
                self.assertEqual(klaus_from_container.age, 20)
