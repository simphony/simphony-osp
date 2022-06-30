"""Test all public API methods.

The public API methods are the methods that are available to the users,
and available in the user documentation.
"""

import os
import shutil
import tempfile
import unittest
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from types import MappingProxyType
from typing import Hashable

from rdflib import RDFS, SKOS, XSD, Graph, Literal, URIRef

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.tools import sparql
from simphony_osp.tools.pico import install, namespaces, packages, uninstall
from simphony_osp.utils.pico import pico


class TestSessionAPI(unittest.TestCase):
    """Tests the session class public methods."""

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.default_ontology
        Session.default_ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.default_ontology = cls.prev_default_ontology

    def test_identifier(self):
        """Test the identifier attribute of the session."""
        with Session() as session:
            self.assertIsNone(session.identifier)

        with Session(identifier="identifier") as session:
            self.assertEqual(session.identifier, "identifier")
            session.identifier = "bcd"
            self.assertEqual(session.identifier, "bcd")
            session.identifier = None
            self.assertIsNone(session.identifier)

    def test_ontology(self):
        """Test the ontology attribute of a session."""
        self.assertIs(self.ontology.ontology, self.ontology)

        with Session() as session:
            self.assertIs(session.ontology, self.ontology)

        with Session() as ontology:
            with Session(ontology=ontology) as abox:
                self.assertIs(abox.ontology, ontology)

    def test_label_properties(self):
        """Test the label_properties attribute of a session.

        The test also changes the properties and verifies that the session
        reacts as expected.
        """
        from simphony_osp.namespaces import city

        with Session() as session:
            self.assertIsInstance(session.label_properties, tuple)
            self.assertTrue(
                all(isinstance(x, URIRef) for x in session.label_properties)
            )

            fr = city.City(name="Freiburg", coordinates=[0, 0])
            self.assertIsNone(fr.label)

            session.graph.add(
                (
                    fr.iri,
                    SKOS.prefLabel,
                    Literal("Freiburg prefLabel", datatype=None, lang=None),
                )
            )
            session.graph.add(
                (
                    fr.iri,
                    RDFS.label,
                    Literal("Freiburg label", datatype=None, lang=None),
                )
            )

            self.assertEqual(fr.label, "Freiburg prefLabel")

            session.label_properties = (RDFS.label, SKOS.prefLabel)
            self.assertEqual(fr.label, "Freiburg label")

    def test_label_languages(self):
        """Test the label_languages attribute of a session.

        The test also changes the properties and verifies that the session
        reacts as expected.
        """
        from simphony_osp.namespaces import city

        with Session() as session:
            self.assertIsInstance(session.label_languages, tuple)
            self.assertTrue(
                all(isinstance(x, str) for x in session.label_languages)
            )

            fr = city.City(name="Freiburg", coordinates=[0, 0])
            self.assertIsNone(fr.label)

            session.graph.add(
                (
                    fr.iri,
                    SKOS.prefLabel,
                    Literal("Freiburg no language", datatype=None, lang=None),
                )
            )
            session.graph.add(
                (
                    fr.iri,
                    SKOS.prefLabel,
                    Literal("Freiburg German", datatype=None, lang="de"),
                )
            )
            session.graph.add(
                (
                    fr.iri,
                    SKOS.prefLabel,
                    Literal("Freiburg Italian", datatype=None, lang="it"),
                )
            )
            session.graph.add(
                (
                    fr.iri,
                    SKOS.prefLabel,
                    Literal("Freiburg English", datatype=None, lang="en"),
                )
            )

            self.assertEqual(fr.label, "Freiburg English")

            session.label_languages = ("it", "en", "de")
            self.assertEqual(fr.label, "Freiburg Italian")

            session.label_languages = ("jp",)
            self.assertIn(
                fr.label,
                {
                    "Freiburg English",
                    "Freiburg Italian",
                    "Freiburg German",
                    "Freiburg no language",
                },
            )

    def test_commit(self):
        """Test the commit method.

        This functionality cannot be tested directly on the session class,
        because sessions themselves do not persist the data. Head to
        `test_wrapper.py` for a test of this functionality.

        Here, it is only checked that the method is callable and raises no
        exceptions.
        """
        with Session() as session:
            session.commit()

    # @unittest.skip("Cannot be directly tested")
    def test_compute(self):
        """Test the compute method.

        This functionality cannot be fully tested directly on the session
        class, because sessions are not attached in general to simulation
        engines. Head to `test_wrapper.py` for actual tests of simulation
        functionality.

        This tests only checks that an attribute error is raised when no
        simulation functionality is available.
        """
        with Session() as session:
            self.assertRaises(AttributeError, session.compute)

    def test_close(self):
        """Test the close method.

        This functionality cannot be fully tested directly on the session
        class, because sessions are not always attached to a graph that can
        be closed. However, some aspects may still be tested.
        """
        # Opening and closing a session should raise no exceptions.
        session = Session()
        session.close()

        # Using the context manager should work.
        with Session():
            pass

        # Closing a session that is being actively used in a context manager
        # should fail.
        with Session() as session:
            self.assertRaises(RuntimeError, session.close)

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
        freiburg.connect(karl, rel=city.hasInhabitant)
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
            all(
                result["citizen"].is_a(next(iter(karl.classes)))
                for result in results
            )
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

    def test_contains(self):
        """Tests the __contains__ method functionality."""
        from simphony_osp.namespaces import city

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        pr = city.City(
            name="Paris", coordinates=[0, 0], iri="http://example.org/Paris"
        )

        with Session() as session_A:
            fr_a = city.City(name="Freiburg", coordinates=[0, 0])
            pr_a = city.City(
                name="Paris",
                coordinates=[0, 0],
                iri="http://example.org/Paris",
            )
            with Session() as session_B:
                fr_b = city.City(name="Freiburg", coordinates=[0, 0])
                pr_b = city.City(
                    name="Paris",
                    coordinates=[0, 0],
                    iri="http://example.org/Paris",
                )

                self.assertNotIn(fr, session_A)
                self.assertNotIn(pr, session_A)
                self.assertIn(fr_a, session_A)
                self.assertIn(pr_a, session_A)
                self.assertNotIn(fr_b, session_A)
                self.assertNotIn(pr_b, session_A)

                self.assertNotIn(fr, session_B)
                self.assertNotIn(pr, session_B)
                self.assertNotIn(fr_a, session_B)
                self.assertNotIn(pr_a, session_B)
                self.assertIn(fr_b, session_B)
                self.assertIn(pr_b, session_B)

    def test_iter(self):
        """Tests the __iter__ method functionality."""
        from simphony_osp.namespaces import city

        with Session() as session:
            self.assertSetEqual(set(session), set())
            fr = city.City(name="Freiburg", coordinates=[100, 5])
            self.assertSetEqual(set(session), {fr})
            lena = city.Citizen(name="Lena", age=90)
            bob = city.Citizen(name="Bob", age=2)
            self.assertSetEqual(set(session), {fr, lena, bob})
            session.delete(fr, bob)
            self.assertSetEqual(set(session), {lena})
            session.delete(lena)
            self.assertSetEqual(set(session), set())

    def test_bool(self):
        """Tests the bool method functionality.

        Should always return True.
        """
        self.assertTrue(Session())

    def test_len(self):
        """Tests the __len__ method functionality."""
        from simphony_osp.namespaces import city

        with Session() as session:
            self.assertEqual(len(session), 0)
            city.City(name="Freiburg", coordinates=[0, 0])
            city.City(
                name="Freiburg",
                coordinates=[0, 0],
                iri="http://example.org/Freiburg",
            )
            city.City(
                name="Freiburg",
                coordinates=[0, 0],
                iri="http://example.org/Freiburg",
            )
            self.assertEqual(len(session), 2)

    def test_from_identifier(self):
        """Tests the from_identifier method."""
        # TODO: skipped so far because this method is used all over
        #  SimPhoNy, very unlikely to be failing.
        pass

    def test_from_identifier_typed(self):
        """Tests the from_identifier_typed method."""
        # TODO: skipped so far because this method is used all over
        #  SimPhoNy, very unlikely to be failing.
        pass

    def test_from_label(self):
        """Tests the from_label method."""
        from simphony_osp.namespaces import city

        self.ontology.lock()
        with self.ontology as ontology:
            citizens = ontology.from_label("Citizen")
            self.assertSetEqual(citizens, {city.Citizen})
            cities = ontology.from_label("City")
            self.assertSetEqual(cities, {city.City})
        self.ontology.unlock()

        with Session() as session:
            citizen_1 = city.Citizen(name="Cz1", age=25)
            citizen_2 = city.Citizen(name="Cz2", age=25)
            self.assertRaises(KeyError, session.from_label, "Some label")
            citizen_1.label = "Label 1"
            citizen_1.label_lang = "en"
            citizen_2.label = "Label 2"
            citizen_2.label_lang = "jp"
            self.assertSetEqual(session.from_label("Label 1"), {citizen_1})
            self.assertSetEqual(session.from_label("Label 2"), {citizen_2})
            self.assertRaises(
                KeyError, session.from_label, "LabeL 1", None, True
            )
            self.assertSetEqual(
                session.from_label("Label 1", case_sensitive=False),
                {citizen_1},
            )
            self.assertRaises(KeyError, session.from_label, "Label 2", "en")
            self.assertSetEqual(
                session.from_label("Label 2", "jp"), {citizen_2}
            )

            citizen_1.label = "Label"
            citizen_2.label = "label"
            self.assertSetEqual(
                session.from_label("Label"), {citizen_1, citizen_2}
            )

    def test_add(self):
        """Test the session's add method.

        Lets the user bring ontology entities from other sessions.
        """
        from simphony_osp.namespaces import city, owl

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        klaus = city.Citizen(name="Klaus", age=59)
        fr[city.hasInhabitant] = klaus

        with Session() as session:
            self.assertEqual(len(session), 0)
            fr_in_session = session.add(fr)
            self.assertEqual(len(session), 1)
            session.add(klaus)
            self.assertEqual(len(session), 2)
            self.assertEqual(len(fr_in_session[owl.topObjectProperty]), 0)

        with Session() as session:
            fr_in_session, klaus_in_session = session.add(fr, klaus)
            self.assertEqual(len(session), 2)
            self.assertEqual(len(fr_in_session[owl.topObjectProperty]), 1)
            self.assertEqual(
                fr_in_session[city.hasInhabitant].any(), klaus_in_session
            )

        with Session():
            klaus_outer = city.Citizen(
                name="Klaus outer", age=20, iri=klaus.iri
            )
            with Session() as session_inner:
                self.assertEqual(len(session_inner), 0)
                fr_s, kl_s = session_inner.add(fr, klaus)
                self.assertEqual(len(session_inner), 2)
                self.assertEqual(len(fr_s[owl.topObjectProperty]), 1)
                self.assertEqual(fr_s[city.hasInhabitant].any(), kl_s)
                self.assertRaises(RuntimeError, session_inner.add, klaus_outer)
                self.assertEqual(kl_s.age, 59)
                self.assertEqual(kl_s.name, "Klaus")
                session_inner.add(klaus_outer, exists_ok=True)
                self.assertEqual(kl_s.age, 20)
                self.assertEqual(kl_s.name, "Klaus outer")
                session_inner.add(klaus, exists_ok=True, merge=True)
                self.assertRaises(RuntimeError, lambda: kl_s.age)
                self.assertRaises(RuntimeError, lambda: kl_s.name)
                self.assertSetEqual(kl_s[city.age], {20, 59})
                self.assertSetEqual(
                    kl_s[city["name"]], {"Klaus", "Klaus outer"}
                )
                session_inner.add(klaus, exists_ok=True, merge=False)
                self.assertEqual(kl_s.age, 59)
                self.assertEqual(kl_s.name, "Klaus")

    def test_delete(self):
        """Test the session's delete method.

        Lets the user delete ontology entities.
        """
        from simphony_osp.namespaces import city

        klaus_outside = city.Citizen(name="Klaus", age=59)

        with Session() as session:
            fr = city.City(name="Freiburg", coordinates=[0, 0])
            klaus = city.Citizen(name="Klaus", age=59)
            fr[city.hasInhabitant] = klaus
            self.assertEqual(len(session), 2)
            self.assertEqual(len(fr[city.hasInhabitant]), 1)
            self.assertRaises(ValueError, session.delete, klaus_outside)
            session.delete(klaus)
            self.assertEqual(len(fr[city.hasInhabitant]), 0)
            self.assertEqual(len(session), 1)

    def test_clear(self):
        """Tests the clear method of the session.

        Gets rid of all the ontology entities in the session.
        """
        from simphony_osp.namespaces import city

        with Session() as session:
            fr = city.City(name="Freiburg", coordinates=[0, 0])
            klaus = city.Citizen(name="Klaus", age=59)
            fr[city.hasInhabitant] = klaus
            self.assertEqual(len(session), 2)
            session.clear()
            self.assertEqual(len(session), 0)

    def test_as_ontology(self):
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

        # Test the `get_namespace` method.
        self.assertRaises(KeyError, ontology.get_namespace, "fake")
        city_namespace = ontology.get_namespace("city")
        self.assertTrue(isinstance(city_namespace, OntologyNamespace))
        self.assertEqual(city_namespace.name, "city")
        self.assertEqual(
            city_namespace.iri, URIRef("https://www.simphony-project.eu/city#")
        )

        # Test the `graph` property.
        self.assertTrue(isinstance(ontology.graph, Graph))


class TestOntologyAPICity(unittest.TestCase):
    """Test the ontology API using the city ontology."""

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and City.
        """
        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.default_ontology
        Session.default_ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.default_ontology = cls.prev_default_ontology

    def test_attribute(self):
        """Tests the OntologyAttribute subclass.

        Includes methods inherited from OntologyEntity.
        """
        from simphony_osp.namespaces import city, owl

        name = city["name"]
        age = city.age
        number = city.number

        # Test with city:name attribute.
        self.assertTrue(isinstance(name, OntologyAttribute))

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
        # TODO: Test setter

        # Test `namespace` property.
        self.assertEqual(name.namespace, city)

        # Test `session` property.
        self.assertIs(name.session, self.ontology)
        # TODO: Test setter

        # Test `direct_superclasses` property.
        self.assertSetEqual(set(), name.direct_superclasses)

        # Test `direct_subclasses` property.
        self.assertSetEqual(set(), name.direct_subclasses)

        # Test `superclasses` property.
        self.assertSetEqual({name, owl.topDataProperty}, name.superclasses)

        # Test `subclasses` property.
        self.assertSetEqual({name}, name.subclasses)

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

        # Test `__bool__` method.
        self.assertTrue(name)

        # Test `datatype` property.
        self.assertEqual(XSD.string, name.datatype)
        self.assertEqual(
            city.age.datatype,
            XSD.integer,
        )

    def test_oclass(self):
        """Tests the OntologyClass subclass.

        Does NOT include methods inherited from OntologyEntity. Such methods
        were already tested in `test_attribute`.
        """
        from simphony_osp.namespaces import city

        person = city.Person

        # Test with city:Person class.
        self.assertTrue(isinstance(person, OntologyClass))

        # Test the `attributes` property.
        self.assertDictEqual(
            {city.age: None, city["name"]: None}, dict(person.attributes)
        )

        # Test the `axioms` property.
        self.assertEqual(4, len(person.axioms))

        # Test `__call__` method.
        self.assertTrue(
            isinstance(person(name="Person name", age=50), OntologyIndividual)
        )

    def test_oclass_composition(self):
        """Tests the Composition subclass.

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
        from simphony_osp.namespaces import city

        has_worker = city.hasWorker
        has_inhabitant = city.hasInhabitant

        # Test with city:hasWorker relationship.
        self.assertTrue(isinstance(has_worker, OntologyRelationship))

        # Test `inverse` method.
        self.assertEqual(has_worker.inverse, city.worksIn)

        # Test with city:hasInhabitant relationship.
        self.assertTrue(isinstance(has_inhabitant, OntologyRelationship))

        # Test `inverse` method.
        self.assertEqual(has_inhabitant.inverse, None)

    def test_individual(self):
        """Tests the OntologyIndividual subclass.

        DOES include methods inherited from OntologyEntity.
        """
        from simphony_osp.namespaces import city, owl

        # Test creating new individuals.
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

        # Test the class related methods `classes`, `is_a`.
        self.assertIsInstance(marc, OntologyIndividual)
        self.assertIsInstance(marc.classes, frozenset)
        self.assertSetEqual(set(marc.classes), {city.Citizen})
        self.assertTrue(marc.is_a(city.Citizen))
        self.assertTrue(marc.is_a(city.LivingBeing))
        self.assertTrue(marc.is_a(city.Person))
        self.assertFalse(marc.is_a(city.City))
        self.assertFalse(marc.is_a(city.ArchitecturalStructure))
        marc.classes = {city.ArchitecturalStructure, city.Citizen}
        self.assertSetEqual(
            set(marc.classes), {city.ArchitecturalStructure, city.Citizen}
        )
        self.assertSetEqual(
            set(marc.superclasses),
            {
                city.ArchitecturalStructure,
                city.Citizen,
                owl.Thing,
                city.Person,
                city.GeographicalPlace,
                city.LivingBeing,
            },
        )
        marc.classes = {city.Citizen}

        # Test the `__dir__` method.
        self.assertTrue("age" in dir(marc))

        # Test the `_ipython_key_completions` method.
        self.assertSetEqual(freiburg[city.hasInhabitant], set())
        self.assertRaises(KeyError, lambda: freiburg["has inhabitant"])
        self.assertNotIn(
            "has inhabitant", freiburg._ipython_key_completions_()
        )
        freiburg[city.hasInhabitant] = sveta
        self.assertSetEqual(freiburg["has inhabitant"], {sveta})
        self.assertIn("has inhabitant", freiburg._ipython_key_completions_())

        # Test the `__getattr__` and `__setattr__` methods.
        self.assertEqual(25, marc.age)
        marc.age = "30"
        self.assertEqual(30, marc.age)
        marc.age = 25
        marc[city.age] += 55
        self.assertRaises(RuntimeError, lambda: marc.age)
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
        self.assertSetEqual(marc["age"], {25})
        freiburg[city.hasInhabitant] = marc
        self.assertEqual(freiburg[city.hasInhabitant].one(), marc)
        freiburg[city.hasInhabitant] += {sveta}
        self.assertSetEqual(freiburg[city.hasInhabitant], {marc, sveta})
        self.assertSetEqual(freiburg["hasInhabitant"], {marc, sveta})
        self.assertSetEqual(freiburg["has inhabitant"], {marc, sveta})
        self.assertRaises(KeyError, lambda z: freiburg[z], "has Inhabitant")
        freiburg[city.hasInhabitant] -= {marc}
        self.assertSetEqual(freiburg[city.hasInhabitant], {sveta})
        freiburg[city.hasInhabitant].clear()
        self.assertSetEqual(freiburg[city.hasInhabitant], set())
        self.assertSetEqual(freiburg[city["name"]], {"Freiburg"})
        self.assertSetEqual(freiburg["name"], {"Freiburg"})
        self.assertRaises(KeyError, lambda z: freiburg[z], "Name")
        self.assertRaises(
            KeyError, freiburg.__setitem__, "has inhabitant", {marc, sveta}
        )
        freiburg[city.hasInhabitant] = {marc}
        freiburg["has inhabitant"] += sveta
        self.assertSetEqual(freiburg["hasInhabitant"], {marc, sveta})
        freiburg[city.hasInhabitant].clear()
        self.assertSetEqual(freiburg[city.hasInhabitant], set())
        freiburg["name"].clear()
        self.assertSetEqual(freiburg["name"], set())
        freiburg["name"] = "Freiburg"
        self.assertEqual(freiburg.name, "Freiburg")
        # More detailed tests of this functionality available in
        # `test_bracket_notation`.

        # Test `connect` method of ontology individuals.
        self.assertRaises(TypeError, freiburg.connect, "a string")
        self.assertRaises(TypeError, freiburg.connect, altstadt)
        freiburg.connect(altstadt, rel=city.hasPart)
        self.assertEqual(freiburg.get(altstadt).uid, altstadt.uid)
        altstadt.connect(dreherstrasse, rel=city.hasPart)
        freiburg.connect(marc, rel=city.hasInhabitant)
        freiburg.connect(sveta, rel=city.hasInhabitant.identifier)
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        self.assertSetEqual({dreherstrasse}, altstadt[city.hasPart])
        x = freiburg.connect(paris, rel=owl.topObjectProperty)
        self.assertIsNone(x)
        with Session():
            pr = city.City(name="Paris", coordinates=[0, 0])
            self.assertRaises(
                RuntimeError,
                lambda p: pr.connect(p, rel=city.hasInhabitant),
                marc,
            )

        # Test `disconnect` method of ontology individuals.
        self.assertRaises(TypeError, freiburg.disconnect, 518)
        # remove()
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.disconnect()
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        # remove(*individuals)
        freiburg[city.hasInhabitant] = {marc, sveta}
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.disconnect(marc)
        self.assertSetEqual({sveta}, freiburg[city.hasInhabitant])
        freiburg.disconnect(sveta)
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        freiburg[city.hasInhabitant] = {marc, sveta}
        # remove(rel=___)
        freiburg[city.hasInhabitant] = {marc, sveta}
        freiburg[city.hasPart] = {altstadt}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.disconnect(rel=city.hasPart)
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        self.assertSetEqual(set(), freiburg[city.hasPart])
        # remove(oclass=___)
        freiburg[city.hasPart] = {altstadt}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.disconnect(oclass=city.Citizen)
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        # remove(*individuals, rel=___)
        freiburg[city.hasInhabitant] = {marc, sveta}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({marc, sveta}, freiburg[city.hasInhabitant])
        freiburg.disconnect(marc, sveta, rel=city.hasInhabitant)
        self.assertSetEqual(set(), freiburg[city.hasInhabitant])
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        # remove(rel=___, oclass=___)
        freiburg[city.hasInhabitant] = {marc, sveta}
        freiburg[city.hasInhabitant] += {altstadt}
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual(
            {marc, sveta, altstadt}, freiburg[city.hasInhabitant]
        )
        freiburg.disconnect(rel=city.hasInhabitant, oclass=city.Citizen)
        self.assertSetEqual({altstadt}, freiburg[city.hasPart])
        self.assertSetEqual({altstadt}, freiburg[city.hasInhabitant])
        # restore city configuration for next tests
        freiburg[city.hasInhabitant] = {marc, sveta}
        freiburg[owl.topObjectProperty] += paris

        # Test `get` method of ontology individuals.
        # test exceptions
        self.assertRaises(TypeError, freiburg.get, 518)
        self.assertRaises(TypeError, freiburg.get, oclass=city.hasInhabitant)
        self.assertRaises(TypeError, freiburg.get, rel=city.Citizen)
        with Session() as session:
            sv = session.add(sveta)
            self.assertRaises(RuntimeError, freiburg.get, sv)
        # get()
        self.assertSetEqual({marc, sveta, altstadt, paris}, freiburg.get())
        # get(*individuals)
        self.assertEqual(marc, freiburg.get(marc))
        self.assertEqual(sveta, freiburg.get(sveta.identifier))
        self.assertEqual(sveta, freiburg.get(str(sveta.identifier)))
        self.assertTupleEqual((sveta, marc), freiburg.get(sveta, marc))
        self.assertIsNone(freiburg.get("http://example.org/individual"))
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
        self.assertIsNone(freiburg.get(sveta, oclass=city.Neighborhood))
        # get(*individuals, rel=___)
        self.assertEqual(marc, freiburg.get(marc, rel=city.hasInhabitant))
        self.assertIsNone(freiburg.get(marc, rel=city.hasPart))
        # get(rel=___, oclass=___)
        self.assertSetEqual(
            {marc, sveta},
            freiburg.get(rel=city.hasInhabitant, oclass=city.Citizen),
        )
        self.assertSetEqual(
            set(),
            freiburg.get(rel=city.hasInhabitant, oclass=city.City),
        )
        # return_rel=True
        ((get_marc, get_marc_rel),) = freiburg.get(marc, return_rel=True)
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
        # test exceptions
        self.assertRaises(TypeError, freiburg.iter, 518)
        self.assertRaises(TypeError, freiburg.iter, oclass=city.hasInhabitant)
        self.assertRaises(TypeError, freiburg.iter, rel=city.Citizen)
        with Session() as session:
            sv = session.add(sveta)
            self.assertRaises(RuntimeError, freiburg.iter, sv)
        self.assertSetEqual(
            {marc, sveta, altstadt, paris}, set(freiburg.iter())
        )
        # iter()
        self.assertSetEqual(
            {marc, sveta, altstadt, paris}, set(freiburg.iter())
        )
        # iter(*individuals)
        self.assertSetEqual({marc}, set(freiburg.iter(marc)))
        self.assertSetEqual({sveta}, set(freiburg.iter(sveta.identifier)))
        self.assertEqual({sveta}, set(freiburg.iter(str(sveta.identifier))))
        self.assertTupleEqual((sveta, marc), tuple(freiburg.iter(sveta, marc)))
        self.assertSetEqual(
            {None}, set(freiburg.iter("http://example.org/individual"))
        )
        # iter(rel=___)
        self.assertSetEqual(
            {marc, sveta}, set(freiburg.iter(rel=city.hasInhabitant))
        )
        self.assertSetEqual(
            {marc, sveta, altstadt}, set(freiburg.iter(rel=city.encloses))
        )
        # iter(oclass=___)
        self.assertSetEqual(
            {marc, sveta}, set(freiburg.iter(oclass=city.Citizen))
        )
        self.assertSetEqual(set(), set(freiburg.iter(oclass=city.Building)))
        self.assertSetEqual(
            {sveta, marc}, set(freiburg.iter(oclass=city.Person))
        )
        self.assertSetEqual(
            set(), set(freiburg.iter(oclass=city.ArchitecturalStructure))
        )
        self.assertSetEqual(
            {None}, set(freiburg.iter(sveta, oclass=city.Neighborhood))
        )
        # iter(*individuals, rel=___)
        self.assertSetEqual(
            {marc}, set(freiburg.iter(marc, rel=city.hasInhabitant))
        )
        self.assertSetEqual({None}, set(freiburg.iter(marc, rel=city.hasPart)))
        # return_rel=True
        get_marc, get_marc_rel = next(freiburg.iter(marc, return_rel=True))
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

        # Test `attributes` method of individuals.
        self.assertIsInstance(marc.attributes, MappingProxyType)
        self.assertDictEqual(
            dict(marc.attributes), {city["name"]: {"Marc"}, city.age: {25}}
        )

    def test_namespace(self):
        """Tests the OntologyNamespace class."""
        from simphony_osp.namespaces import city

        self.assertTrue(isinstance(city, OntologyNamespace))

        # Test the `__init__` method.
        city_again = OntologyNamespace(
            URIRef("https://www.simphony-project.eu/city#"),
            ontology=self.ontology,
            name="city",
        )
        self.assertTrue(isinstance(city, OntologyNamespace))

        # Test the `name` property.
        self.assertEqual(city.name, "city")

        # Test the `iri` property.
        self.assertEqual(
            city.iri, URIRef("https://www.simphony-project.eu/city#")
        )

        # Test the `ontology` property.
        self.assertIs(city.ontology, self.ontology)

        # Test the `__eq__` method.
        self.assertEqual(city_again, city)
        empty_ontology = Session(ontology=True)
        city_empty_ontology = OntologyNamespace(
            URIRef("https://www.simphony-project.eu/city#"),
            ontology=empty_ontology,
            name="city",
        )
        self.assertNotEqual(city, city_empty_ontology)
        city_different_iri = OntologyNamespace(
            URIRef("https://www.simphony-project.eu/city_dif#"),
            ontology=self.ontology,
            name="city_dif",
        )
        self.assertNotEqual(city, city_different_iri)

        # Test the `__hash__` method.
        self.assertNotEqual(city.__hash__(), city_empty_ontology.__hash__())
        self.assertNotEqual(city.__hash__(), city_different_iri.__hash__())

        # Test the `__getattr__` method.
        has_inhabitant = self.ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#hasInhabitant")
        )
        self.assertEqual(has_inhabitant, getattr(city, "hasInhabitant"))
        self.assertRaises(
            AttributeError, lambda x: getattr(city, x), "does_not_exist"
        )

        # Test the `__getitem__` method.
        name = self.ontology.from_identifier(
            URIRef("https://www.simphony-project.eu/city#name")
        )
        self.assertEqual(name, city["name"])

        # Test the `__dir__` method.
        self.assertIn("hasMajor", dir(city))
        self.assertIn("hasInhabitant", dir(city))

        # Test the `_ipython_key_completions_` method.
        self.assertIn("hasMajor", city._ipython_key_completions_())
        self.assertIn("hasInhabitant", city._ipython_key_completions_())
        self.assertIn("has inhabitant", city._ipython_key_completions_())

        # Test the `__iter__` method.
        self.assertEqual(28, len(tuple(city)))
        self.assertIn(name, tuple(city))
        self.assertIn(has_inhabitant, tuple(city))

        # Test the `__contains__` method.
        self.assertIn(name, city)
        self.assertIn(has_inhabitant, city)
        self.assertIn(name.iri, city)
        self.assertIn(has_inhabitant.iri, city)
        self.assertNotIn(URIRef("other:some_iri"), city)

        # Test the `__len__` method.
        self.assertEqual(28, len(city))

        # Test the `get` method.
        self.assertEqual(city.hasInhabitant, city.get("has inhabitant"))
        self.assertEqual(city.hasInhabitant, city.get("hasInhabitant"))
        self.assertRaises(KeyError, city.get, "not existing")
        self.assertEqual("Text", city.get("not existing", "Text"))
        self.assertEqual(
            city.hasInhabitant, city.get("has inhabitant", "Text")
        )

        # Test the `from_suffix` method.
        self.assertEqual(city.hasInhabitant, city.from_suffix("hasInhabitant"))
        self.assertRaises(KeyError, city.from_suffix, "a_suffix")
        self.assertRaises(ValueError, city.from_suffix, "has inhabitant")

        # Test the `from_iri` method.
        self.assertEqual(
            city.hasInhabitant, city.from_iri(city.hasInhabitant.iri)
        )
        self.assertEqual(
            city.hasInhabitant, city.from_iri(str(city.hasInhabitant.iri))
        )
        self.assertRaises(
            KeyError,
            city.from_iri,
            "http://example.org/namespace#hasInhabitant",
        )
        self.assertRaises(
            KeyError,
            city.from_iri,
            "https://www.simphony-project.eu/city#hasinhabitant",
        )
        self.assertRaises(
            ValueError,
            city.from_iri,
            "https://www.simphony-project.eu/city#has " "Inhabitant",
        )

        # Test the `from_label` method.
        self.assertRaises(KeyError, city.from_label, "Name", None, True)
        self.assertEqual(city["name"], city.from_label("name"))
        self.assertEqual(city["name"], city.from_label("Name"))
        self.assertRaises(KeyError, city.from_label, "Name", "jp", False)

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

        # Test annotations -> goto
        # TestOntologyAPIFOAF.test_bracket_notation.

        # Test attributes -> goto
        # TestOntologyAPIFOAF.test_bracket_notation.


class TestOntologyAPIFOAF(unittest.TestCase):
    """Test the ontology API using the FOAF ontology.

    Tests only features not tested with the City ontology.
    """

    # TODO: Extend the City ontology with so that this
    #  test can be merged with `TestOntologyAPICity`.

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and FOAF.
        """
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yml", delete=False
        ) as file:
            foaf_url = (
                "https://web.archive.org/web/20220627164615/"
                "http://xmlns.com/foaf/spec/index.rdf"
            )
            foaf_modified: str = f"""
            identifier: foaf
            format: xml
            namespaces:
              foaf: http://xmlns.com/foaf/0.1/
            ontology_file: {foaf_url}
            """
            file.write(foaf_modified)
            file.seek(0)
            yml_path = file.name

        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser(yml_path))
        cls.prev_default_ontology = Session.default_ontology
        Session.default_ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.default_ontology = cls.prev_default_ontology

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
        from simphony_osp.namespaces import foaf

        # Test annotation of ontology individuals.
        group = foaf.Group()
        person = foaf.Person()
        another_person = foaf.Person()
        one_more_person = foaf.Person()
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

        # --- Test annotations ---
        # TODO

        # Test relationships -> goto
        # test_api_city.TestAPICity.test_bracket_notation.


class TestPico(unittest.TestCase):
    """Tests the usage of pico."""

    prev_default_ontology: Session
    path: Path

    def setUp(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and FOAF.
        """
        self.path = Path(".TEST_OSP_CORE_INSTALLATION").absolute()
        os.makedirs(self.path, exist_ok=True)

        pico.set_default_installation_path(self.path)

    def tearDown(self):
        """Restore the previous default TBox."""
        pico.set_default_installation_path(None)
        shutil.rmtree(self.path)

    def test_install(self):
        """Test the installation of ontologies."""
        self.assertRaises(
            ModuleNotFoundError,
            import_module,
            "city",
            "simphony_osp.namespaces",
        )

        install("city")

        from simphony_osp.namespaces import city

        self.assertTrue(city.City)

    def test_uninstall(self):
        """Test the uninstallation of ontologies."""
        import simphony_osp.namespaces as namespaces_module

        # Install the ontology first and guarantee that it worked.
        self.assertRaises(
            ModuleNotFoundError,
            import_module,
            "city",
            "simphony_osp.namespaces",
        )
        install("city")

        from simphony_osp.namespaces import city

        self.assertTrue(city.City)

        # Now test uninstallation.
        uninstall("city")
        self.assertRaises(
            ModuleNotFoundError,
            import_module,
            "city",
            "simphony_osp.namespaces",
        )
        self.assertRaises(
            AttributeError, lambda: getattr(namespaces_module, "city")
        )
        self.assertRaises(AttributeError, lambda: city.City)

        # Test that reinstalling makes the existing namespace work again.
        install("city")
        self.assertTrue(city.City)

    def test_packages(self):
        """Test listing installed packages."""
        self.assertTupleEqual(tuple(), packages())
        install("city")
        self.assertTupleEqual(("city",), packages())
        uninstall("city")
        self.assertTupleEqual(tuple(), packages())

    def test_namespaces(self):
        """Test listing ontology namespaces."""
        self.assertDictEqual(
            {
                "simphony": URIRef(
                    "https://www.simphony-project.eu/simphony#"
                ),
                "owl": URIRef("http://www.w3.org/2002/07/owl#"),
                "rdfs": URIRef("http://www.w3.org/2000/01/rdf-schema#"),
            },
            {ns.name: ns.iri for ns in namespaces()},
        )

        install("city")

        self.assertDictEqual(
            {
                "simphony": URIRef(
                    "https://www.simphony-project.eu/simphony#"
                ),
                "owl": URIRef("http://www.w3.org/2002/07/owl#"),
                "rdfs": URIRef("http://www.w3.org/2000/01/rdf-schema#"),
                "city": URIRef("https://www.simphony-project.eu/city#"),
            },
            {ns.name: ns.iri for ns in namespaces()},
        )


class TestContainer(unittest.TestCase):
    """Tests the containers."""

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and City.
        """
        ontology = Session(identifier="test-tbox", ontology=True)
        ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.default_ontology
        Session.default_ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.default_ontology = cls.prev_default_ontology

    def test_container(self):
        """Test the container ontology individual."""
        from simphony_osp.namespaces import city, simphony

        container = simphony.Container()

        self.assertIsNone(container.operations.opens_in)
        self.assertIsNone(container.operations.session_linked)
        self.assertFalse(container.operations.is_open)
        self.assertSetEqual(set(), set(container.operations.references))
        self.assertEqual(len(container.operations.references), 0)
        self.assertEqual(container.operations.num_references, 0)

        with container as context:
            self.assertIs(
                Session.get_default_session(), context.session_linked
            )
            self.assertIs(
                Session.get_default_session(),
                container.operations.session_linked,
            )
            self.assertTrue(context.is_open)
            self.assertTrue(container.operations.is_open)
        self.assertIsNone(container.operations.session_linked)
        self.assertFalse(container.operations.is_open)

        self.assertEqual(container.operations.num_members, 0)
        self.assertSetEqual(set(), set(container.operations.members))

        session = Session()
        container.operations.opens_in = session
        with container as context:
            self.assertTrue(context.is_open)
            self.assertTrue(container.operations.is_open)
            self.assertIs(session, context.session_linked)
            self.assertIs(session, container.operations.session_linked)
        self.assertIsNone(container.operations.session_linked)
        self.assertFalse(container.operations.is_open)
        self.assertRaises(
            TypeError,
            lambda x: setattr(container.operations, "opens_in", x),
            8,
        )
        container.operations.opens_in = None

        another_container = simphony.Container()

        another_container.operations.opens_in = container
        # self.assertRaises(RuntimeError, another_container.operations.open)
        container.operations.open()
        with another_container as another_context:
            self.assertIs(
                Session.get_default_session(),
                container.operations.session_linked,
            )
            self.assertIs(
                container.operations.session_linked,
                another_context.session_linked,
            )
            self.assertIs(
                container.operations.session_linked,
                another_container.operations.session_linked,
            )
        container.operations.close()

        fr_session = Session()
        fr = city.City(name="Freiburg", coordinates=[0, 0], session=fr_session)
        container.operations.references = {fr.iri}
        default_session = Session.get_default_session()

        self.assertIn(fr.iri, container.operations.references)
        self.assertEqual(container.operations.num_references, 1)
        with fr_session:
            with container as context:
                self.assertIs(fr_session, context.session_linked)
                self.assertIs(fr_session, container.operations.session_linked)
                self.assertIs(default_session, container.session)
                self.assertEqual(len(context), 1)
                self.assertEqual(container.operations.num_members, 1)
                self.assertSetEqual({fr}, set(context))
                self.assertSetEqual({fr}, set(container.operations.members))
                self.assertIn(fr, context)
                self.assertIn(fr, container.operations.members)

        broken_reference = URIRef("http://example.org/things#something")
        container.operations.references = {broken_reference}
        self.assertIn(broken_reference, container.operations.references)
        self.assertNotIn(fr, container.operations.members)
        self.assertEqual(container.operations.num_references, 1)
        with fr_session:
            self.assertEqual(len(set(container.operations.members)), 0)
            self.assertSetEqual(set(), set(container.operations.members))
            self.assertNotIn(fr, container.operations.members)

        container.operations.connect(broken_reference)
        self.assertEqual(container.operations.num_references, 1)
        container.operations.connect(broken_reference)
        self.assertEqual(container.operations.num_references, 1)
        container.operations.disconnect(broken_reference)
        self.assertEqual(container.operations.num_references, 0)

        with fr_session:
            container.operations.add(fr)
            self.assertSetEqual({fr}, set(container.operations.members))
            self.assertTrue(
                all(
                    x.session is fr_session
                    for x in container.operations.members
                )
            )
            container.operations.remove(fr)
            self.assertEqual(container.operations.num_references, 0)
            self.assertSetEqual(set(), set(container.operations.members))
            container.operations.add(fr)
            self.assertSetEqual({fr}, set(container.operations.members))

        with container as context:
            self.assertEqual(context.num_references, 1)
            self.assertEqual(container.operations.num_references, 1)
            self.assertSetEqual(set(), set(context))
            self.assertSetEqual(set(), set(container.operations.members))

        with fr_session:
            with container as context:
                self.assertSetEqual({fr}, set(context))
                self.assertSetEqual({fr}, set(container.operations.members))
                pr = city.City(name="Paris", coordinates=[0, 0])
                self.assertSetEqual({fr, pr}, set(context))
                self.assertSetEqual(
                    {fr, pr}, set(container.operations.members)
                )

    def test_container_multiple_sessions(self):
        """Test opening the container in different sessions.

        Each session is meant to contain a different version of the same
        individual.
        """
        from simphony_osp.namespaces import city, simphony

        container = simphony.Container()

        default_session = Session.get_default_session()
        session_1 = Session()
        session_2 = Session()

        klaus = city.Citizen(name="Klaus", age=5)
        session_1.add(klaus)
        session_2.add(klaus)
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

        container.operations.connect(klaus.identifier)

        with container as context:
            klaus_from_container = set(context).pop()
            self.assertEqual(klaus_from_container.age, 5)

        with session_1:
            with container as context:
                klaus_from_container = set(context).pop()
                self.assertEqual(klaus_from_container.age, 10)

        with session_2:
            with container as context:
                klaus_from_container = set(context).pop()
                self.assertEqual(klaus_from_container.age, 20)


if __name__ == "__main__":
    unittest.main()
