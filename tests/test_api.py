"""Test all public API methods.

The public API methods are the methods that are available to the users,
and available in the user documentation.
"""
import io
import json
import os
import shutil
import tempfile
import unittest
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from types import MappingProxyType
from typing import Hashable, Iterable, Iterator, Optional, Tuple, Type, Union

from rdflib import OWL, RDF, RDFS, SKOS, XSD, BNode, Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.individual import (
    MultipleResultsError,
    OntologyIndividual,
    ResultEmptyError,
)
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.tools import branch, export_file, import_file, sparql
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
        """Test the label_predicates attribute of a session.

        The test also changes the properties and verifies that the session
        reacts as expected.
        """
        from simphony_osp.namespaces import city

        with Session() as session:
            self.assertIsInstance(session.label_predicates, tuple)
            self.assertTrue(
                all(isinstance(x, URIRef) for x in session.label_predicates)
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

            session.label_predicates = (RDFS.label, SKOS.prefLabel)
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

    def test_iter_magic(self):
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
            URIRef("https://www.simphony-osp.eu/city#hasInhabitant")
        )
        self.assertTrue(isinstance(has_inhabitant, OntologyRelationship))
        encloses = ontology.from_identifier(
            URIRef("https://www.simphony-osp.eu/city#encloses")
        )
        self.assertTrue(isinstance(encloses, OntologyRelationship))
        has_part = ontology.from_identifier(
            URIRef("https://www.simphony-osp.eu/city#hasPart")
        )
        self.assertTrue(isinstance(has_part, OntologyRelationship))
        name = ontology.from_identifier(
            URIRef("https://www.simphony-osp.eu/city#name")
        )
        self.assertTrue(isinstance(name, OntologyAttribute))

        # Test the `get_namespace` method.
        self.assertRaises(KeyError, ontology.get_namespace, "fake")
        city_namespace = ontology.get_namespace("city")
        self.assertTrue(isinstance(city_namespace, OntologyNamespace))
        self.assertEqual(city_namespace.name, "city")
        self.assertEqual(
            city_namespace.iri, URIRef("https://www.simphony-osp.eu/city#")
        )

        # Test the `graph` property.
        self.assertTrue(isinstance(ontology.graph, Graph))

    def test_iter(self):
        """Tests the `iter` method of the session."""
        from simphony_osp.namespaces import city

        pr = city.City(name="Paris", coordinates=[20, 10])

        with Session() as session:
            fr = city.City(name="Freiburg", coordinates=[100, 5])
            lena = city.Citizen(name="Lena", age=90)
            bob = city.Citizen(name="Bob", age=2)
            stuehlinger = city.Neighborhood(
                name="Stühlinger", coordinates=[100, 6]
            )

            # test exceptions
            self.assertRaises(TypeError, session.iter, 89)
            self.assertRaises(RuntimeError, session.iter, pr)
            self.assertRaises(TypeError, session.iter, oclass=40)

            # iter()
            args = ()
            kwargs = {}
            self.assertIsInstance(session.iter(*args, **kwargs), Iterator)
            self.assertEqual(4, len(tuple(session.iter(*args, **kwargs))))
            self.assertSetEqual(
                {lena, bob, fr, stuehlinger},
                set(session.iter(*args, **kwargs)),
            )

            # iter(oclass=___)
            args = ()
            kwargs = {"oclass": city.Citizen}
            self.assertIsInstance(session.iter(*args, **kwargs), Iterator)
            self.assertEqual(2, len(tuple(session.iter(*args, **kwargs))))
            self.assertSetEqual(
                {lena, bob}, set(session.iter(*args, **kwargs))
            )
            kwargs = {"oclass": city.PopulatedPlace}
            self.assertEqual(2, len(tuple(session.iter(*args, **kwargs))))
            self.assertSetEqual(
                {fr, stuehlinger}, set(session.iter(*args, **kwargs))
            )
            kwargs = {"oclass": city.City}
            self.assertEqual(1, len(tuple(session.iter(*args, **kwargs))))
            self.assertSetEqual({fr}, set(session.iter(*args, **kwargs)))

            # iter(*individuals)
            self.assertIsInstance(session.iter(fr), Iterator)
            self.assertTupleEqual((fr,), tuple(session.iter(fr)))
            self.assertTupleEqual(
                (fr, fr, bob, bob, lena, None, None, None),
                tuple(
                    session.iter(
                        fr,
                        fr,
                        bob,
                        bob.identifier,
                        str(lena.identifier),
                        BNode(),
                        URIRef("http://example.org/id"),
                        "lxc",
                    )
                ),
            )

            # iter(*individuals, oclass=___)
            self.assertIsInstance(session.iter(fr, oclass=city.City), Iterator)
            self.assertTupleEqual(
                (fr,), tuple(session.iter(fr, oclass=city.City))
            )
            self.assertTupleEqual(
                (None,), tuple(session.iter(fr, oclass=city.Citizen))
            )
            self.assertTupleEqual(
                (None, None, bob, bob, lena, None, None, None),
                tuple(
                    session.iter(
                        fr,
                        fr,
                        bob,
                        bob.identifier,
                        str(lena.identifier),
                        BNode(),
                        URIRef("http://example.org/id"),
                        "lxc",
                        oclass=city.Citizen,
                    )
                ),
            )
            self.assertTupleEqual(
                (fr, fr, None, None, None, None, None, None),
                tuple(
                    session.iter(
                        fr,
                        fr,
                        bob,
                        bob.identifier,
                        str(lena.identifier),
                        BNode(),
                        URIRef("http://example.org/id"),
                        "lxc",
                        oclass=city.City,
                    )
                ),
            )

    def test_get(self):
        """Tests the `get` method of the session."""
        from simphony_osp.namespaces import city

        pr = city.City(name="Paris", coordinates=[20, 10])

        with Session() as session:
            fr = city.City(name="Freiburg", coordinates=[100, 5])
            lena = city.Citizen(name="Lena", age=90)
            bob = city.Citizen(name="Bob", age=2)
            stuehlinger = city.Neighborhood(
                name="Stühlinger", coordinates=[100, 6]
            )

            # test exceptions
            self.assertRaises(TypeError, session.get, 89)
            self.assertRaises(RuntimeError, session.get, pr)
            self.assertRaises(TypeError, session.get, oclass=40)

            # get()
            self.assertSetEqual({lena, bob, fr, stuehlinger}, session.get())

            # get(oclass=___)
            self.assertSetEqual({lena, bob}, session.get(oclass=city.Citizen))
            self.assertSetEqual(
                {fr, stuehlinger},
                session.get(oclass=city.PopulatedPlace),
            )
            self.assertSetEqual({fr}, session.get(oclass=city.City))

            # get(*individuals)
            self.assertEqual(fr, session.get(fr))
            self.assertEqual(None, session.get(BNode()))
            self.assertTupleEqual(
                (fr, fr, bob, bob, lena, None, None, None),
                session.get(
                    fr,
                    fr,
                    bob,
                    bob.identifier,
                    str(lena.identifier),
                    BNode(),
                    URIRef("http://example.org/id"),
                    "lxc",
                ),
            )

            # get(*individuals, oclass=___)
            self.assertEqual(fr, session.get(fr, oclass=city.City))
            self.assertEqual(None, session.get(fr, oclass=city.Citizen))
            self.assertTupleEqual(
                (None, None, bob, bob, lena, None, None, None),
                session.get(
                    fr,
                    fr,
                    bob,
                    bob.identifier,
                    str(lena.identifier),
                    BNode(),
                    URIRef("http://example.org/id"),
                    "lxc",
                    oclass=city.Citizen,
                ),
            )
            self.assertTupleEqual(
                (fr, fr, None, None, None, None, None, None),
                session.get(
                    fr,
                    fr,
                    bob,
                    bob.identifier,
                    str(lena.identifier),
                    BNode(),
                    URIRef("http://example.org/id"),
                    "lxc",
                    oclass=city.City,
                ),
            )

    def test_session_set(self):
        """Tests the `SessionSet` objects obtained from the `get` method.

        Note that this whole file `test_api.py` only tests what the user can do
        using the public API. This means that special characteristics of the
        SessionSet are not tested here. Also, many of the methods of the
        `SessionSet` are implicitly tested on `test_get`, such as the
        `__iter__` method. Such details are omitted in this test.
        """
        from simphony_osp.namespaces import city

        pr = city.City(name="Paris", coordinates=[20, 10])

        with Session() as session:
            fr = city.City(name="Freiburg", coordinates=[100, 5])
            lena = city.Citizen(name="Lena", age=90)
            bob = city.Citizen(name="Bob", age=2)
            stuehlinger = city.Neighborhood(
                name="Stühlinger", coordinates=[100, 6]
            )

            # Test `__contains__` method.
            session_set = session.get()
            self.assertNotIn(pr, session_set)
            self.assertIn(fr, session_set)
            self.assertIn(lena, session_set)
            self.assertIn(bob, session_set)
            self.assertIn(stuehlinger, session_set)
            session_set = session.get(oclass=city.Citizen)
            self.assertNotIn(pr, session_set)
            self.assertNotIn(fr, session_set)
            self.assertIn(lena, session_set)
            self.assertIn(bob, session_set)
            self.assertNotIn(stuehlinger, session_set)

            # Test `update` method.
            session_set = session.get()
            session_set.update((fr, lena, bob))
            session_set = session.get(oclass=city.Citizen)
            self.assertRaises(RuntimeError, session_set.update, {fr})
            session_set = session.get()
            br_orig = city.City(
                name="Berlin",
                coordinates=[120, 40],
                iri="http://example.org/cities#Berlin",
            )
            amir_orig = city.Citizen(
                name="Amir", age=50, iri="http://example.org/people#Amir"
            )
            br_orig[city.hasInhabitant] = amir_orig
            with Session():
                br = city.City(
                    name="Berlin",
                    coordinates=[120, 40],
                    iri="http://example.org/cities#Berlin",
                )
                markus = city.Citizen(
                    name="Markus",
                    age=37,
                    iri="http://example.org/people#Markus",
                )
                amir = city.Citizen(
                    name="Amir", age=53, iri="http://example.org/people#Amir"
                )
                br[city.hasInhabitant] = {amir, markus}

                # verify that initial state is coherent
                self.assertIn(amir_orig, session_set)
                self.assertNotIn(amir, session_set)
                self.assertSetEqual(
                    {53},
                    amir[city.age],
                )
                self.assertSetEqual({amir_orig}, br_orig[city.hasInhabitant])
                # update with `amir` and verify state again
                session_set.update({amir})
                self.assertIn(amir_orig, session_set)
                self.assertNotIn(amir, session_set)
                self.assertSetEqual(
                    {50, 53}, amir_orig[city.age]
                )  # existing and new individuals are merged
                self.assertSetEqual({53}, amir[city.age])
                self.assertSetEqual(
                    {amir_orig}, br_orig[city.hasInhabitant]
                )  # updating amir does not break the connection to Berlin
                session_set.update({markus})
                self.assertSetEqual({amir_orig}, br_orig[city.hasInhabitant])
                session_set.update(
                    {markus}
                )  # updating twice does not raise an error

            # Test `intersection_update` method.
            session_set = session.get()
            self.assertTrue(len(session_set) > 4)
            session_set.intersection_update({fr, lena, bob, stuehlinger})
            self.assertSetEqual({fr, lena, bob, stuehlinger}, session_set)
            session_set_class_filter = session.get(oclass=city.Citizen)
            self.assertRaises(
                RuntimeError,
                session_set_class_filter.intersection_update,
                {fr, stuehlinger},
            )
            self.assertSetEqual(
                {fr, lena, bob, stuehlinger}, session_set
            )  # intersection_update failed, no changes expected
            with Session():
                lena_new = city.Citizen(
                    name="Lena", age=23, iri=lena.identifier
                )
                self.assertSetEqual(
                    {90}, lena[city.age]
                )  # in each session there is only one age
                self.assertSetEqual(
                    {23}, lena_new[city.age]
                )  # in each session there is only one age
                session_set.intersection_update({fr, lena_new, stuehlinger})
                self.assertNotEqual(
                    {fr, lena_new, stuehlinger}, session_set
                )  # lena_new belongs to the new session
                self.assertSetEqual(
                    {fr, lena, stuehlinger}, session_set
                )  # lena is the Python object pointing to the old session
                self.assertSetEqual(
                    {23, 90}, lena[city.age]
                )  # in the old session now lena has two ages

            # Test `difference_update` method.
            session_set_class_filter = session.get(oclass=city.Citizen)
            self.assertRaises(
                RuntimeError,
                session_set_class_filter.difference_update,
                {stuehlinger},
            )
            session_set_class_filter.difference_update({pr})
            # no error raised because Paris does not exist on the session
            session_set.difference_update({bob})
            self.assertSetEqual(
                {fr, lena, stuehlinger}, session_set
            )  # nothing happens because Bob's identifier is not in the session
            session_set.difference_update({stuehlinger})
            self.assertSetEqual({fr, lena}, session_set)

            # Test `symmetric_difference_update` method.
            bob = city.Citizen(name="Bob", age=2, iri=bob.identifier)
            stuehlinger = city.Neighborhood(
                name="Stühlinger",
                coordinates=[100, 6],
                iri=stuehlinger.identifier,
            )
            self.assertSetEqual({fr, lena, bob, stuehlinger}, session_set)
            with Session():
                altstadt = city.Neighborhood(
                    name="Altstadt", coordinates=[0, 0]
                )
                session_set_class_filter = session.get(oclass=city.Citizen)
                self.assertRaises(
                    RuntimeError,
                    session_set_class_filter.symmetric_difference_update,
                    {altstadt},
                )  # Altstadt has to be added
                stuhlinger_citizen = city.Citizen(name="Stühlinger", age=18)
                session_set_class_filter = session.get(
                    oclass=city.Neighborhood
                )
                self.assertRaises(
                    RuntimeError,
                    session_set_class_filter.symmetric_difference_update,
                    {stuhlinger_citizen},
                )  # Stühlinger has to be deleted
                br = city.City(
                    name="Berlin",
                    coordinates=[120, 40],
                    iri="http://example.org/cities#Berlin",
                )
                markus = city.Citizen(
                    name="Markus",
                    age=37,
                    iri="http://example.org/people#Markus",
                )
                session_set.symmetric_difference_update(
                    {altstadt, br, markus, bob}
                )
                br = session.from_identifier(br.identifier)
                altstadt = session.from_identifier(altstadt.identifier)
                markus = session.from_identifier(markus.identifier)
                self.assertSetEqual(
                    {fr, br, lena, stuehlinger, markus, altstadt}, session_set
                )

            # Test `one` method.
            session_set = session.get(oclass=city.City)
            self.assertRaises(MultipleResultsError, session_set.one)
            session.delete(br)
            self.assertEqual(fr, session_set.one())
            session_set = session.get(oclass=city.Neighborhood)
            session.delete(altstadt, stuehlinger)
            self.assertRaises(ResultEmptyError, session_set.one)

            # Test `any` method.
            session_set = session.get(oclass=city.Citizen)
            self.assertIn(session_set.any(), {lena, markus})
            session_set = session.get(oclass=city.Neighborhood)
            self.assertIsNone(session_set.any())

            # Test `all` method.
            session_set = session.get()
            self.assertIs(session_set.all(), session_set)

    def test_core_session(self):
        """Tests access and use of the default session."""
        from simphony_osp.namespaces import city
        from simphony_osp.session import Session, core_session

        fr = city.City(name="Freiburg", coordinates=[10, 28])

        self.assertIs(fr.session, core_session)

        with Session() as session:
            pr = city.City(name="Paris", coordinates=[-10, 42])
            self.assertIsNot(fr.session, pr.session)
            self.assertIs(pr.session, session)


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
            URIRef("https://www.simphony-osp.eu/city#name"),
        )

        # Test `iri` property.
        self.assertEqual(
            name.iri, URIRef("https://www.simphony-osp.eu/city#name")
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
            URIRef("https://www.simphony-osp.eu/city#"),
            ontology=self.ontology,
            name="city",
        )
        self.assertTrue(isinstance(city, OntologyNamespace))

        # Test the `name` property.
        self.assertEqual(city.name, "city")

        # Test the `iri` property.
        self.assertEqual(city.iri, URIRef("https://www.simphony-osp.eu/city#"))

        # Test the `ontology` property.
        self.assertIs(city.ontology, self.ontology)

        # Test the `__eq__` method.
        self.assertEqual(city_again, city)
        empty_ontology = Session(ontology=True)
        city_empty_ontology = OntologyNamespace(
            URIRef("https://www.simphony-osp.eu/city#"),
            ontology=empty_ontology,
            name="city",
        )
        self.assertNotEqual(city, city_empty_ontology)
        city_different_iri = OntologyNamespace(
            URIRef("https://www.simphony-osp.eu/city_dif#"),
            ontology=self.ontology,
            name="city_dif",
        )
        self.assertNotEqual(city, city_different_iri)

        # Test the `__hash__` method.
        self.assertNotEqual(city.__hash__(), city_empty_ontology.__hash__())
        self.assertNotEqual(city.__hash__(), city_different_iri.__hash__())

        # Test the `__getattr__` method.
        has_inhabitant = self.ontology.from_identifier(
            URIRef("https://www.simphony-osp.eu/city#hasInhabitant")
        )
        self.assertEqual(has_inhabitant, getattr(city, "hasInhabitant"))
        self.assertRaises(
            AttributeError, lambda x: getattr(city, x), "does_not_exist"
        )

        # Test the `__getitem__` method.
        name = self.ontology.from_identifier(
            URIRef("https://www.simphony-osp.eu/city#name")
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
            "https://www.simphony-osp.eu/city#hasinhabitant",
        )
        self.assertRaises(
            ValueError,
            city.from_iri,
            "https://www.simphony-osp.eu/city#has " "Inhabitant",
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
                "https://web.archive.org/web/20220614185720if_/"
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


class TestBundledOperations(unittest.TestCase):
    """Tests the ontology operations bundled with SimPhoNy."""

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


class TestToolsPico(unittest.TestCase):
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
                "simphony": URIRef("https://www.simphony-osp.eu/simphony#"),
                "owl": URIRef("http://www.w3.org/2002/07/owl#"),
                "rdfs": URIRef("http://www.w3.org/2000/01/rdf-schema#"),
            },
            {ns.name: ns.iri for ns in namespaces()},
        )

        install("city")

        self.assertDictEqual(
            {
                "simphony": URIRef("https://www.simphony-osp.eu/simphony#"),
                "owl": URIRef("http://www.w3.org/2002/07/owl#"),
                "rdfs": URIRef("http://www.w3.org/2000/01/rdf-schema#"),
                "city": URIRef("https://www.simphony-osp.eu/city#"),
            },
            {ns.name: ns.iri for ns in namespaces()},
        )


class TestToolsGeneral(unittest.TestCase):
    """Tests the methods from `simphony_osp.tools.general."""

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

    def test_branch(self):
        """Tests the `branch` function."""
        from simphony_osp.namespaces import city, owl
        from simphony_osp.tools import branch

        fr = city.City(name="Freiburg", coordinates=[1, 20])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        klaus = city.Citizen(name="Klaus", age=1)
        branch_output = branch(fr, marc, sveta, rel=city.hasInhabitant)
        self.assertIs(branch_output, fr)
        self.assertIn(marc, fr[owl.topObjectProperty])
        self.assertIn(sveta, fr[owl.topObjectProperty])
        self.assertIn(marc, fr[city.hasInhabitant])
        self.assertIn(sveta, fr[city.hasInhabitant])
        self.assertNotIn(marc, fr[city.hasWorker])

        pr = branch(
            city.City(name="Paris", coordinates=[0, 0]),
            branch(marc, klaus, rel=city.hasChild),
            branch(sveta, klaus, rel=city.hasChild),
            rel=city.hasInhabitant,
        )

        self.assertIn(marc, pr[city.hasInhabitant])
        self.assertIn(klaus, marc[city.hasChild])
        self.assertIn(sveta, klaus[city.hasChild].inverse)

    def test_relationships_between(self):
        """Tests the `relationships_between` function."""
        from simphony_osp.namespaces import city, owl
        from simphony_osp.tools import relationships_between

        fr = city.City(name="Freiburg", coordinates=[1, 20])
        marc = city.Citizen(name="Marc", age=25)

        fr[city.hasMajor] += marc
        fr[city.hasInhabitant] += marc
        fr[owl.topObjectProperty] += marc
        marc[city.hasChild] += fr
        self.assertSetEqual(
            {city.hasMajor, city.hasInhabitant},
            relationships_between(fr, marc),
        )
        self.assertSetEqual({city.hasChild}, relationships_between(marc, fr))


class TestToolsImportExport(unittest.TestCase):
    """Tests importing and exporting ontology individuals.

    The loading process returns individuals in the files. Some of the
    known information about the individuals in the file is tested against
    the loaded data.
    """

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS, SKOS and an ontology
        specifically crafted for this test case.
        """
        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser("city"))
        cls.ontology.load_parser(OntologyParser.get_parser("skos"))
        cls.ontology.load_parser(
            OntologyParser.get_parser(
                str(Path(__file__).parent / "test_api_importexport.yml")
            )
        )
        cls.prev_default_ontology = Session.default_ontology
        Session.default_ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.default_ontology = cls.prev_default_ontology

    def test_application_rdf_xml(self):
        """Test importing and exporting the `application/rdf+xml` mime type."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.owl"
            )
            loaded_objects = import_file(
                test_data_path, format="application/rdf+xml"
            )
            self.data_integrity(session, loaded_objects, label="import")
            exported_file = io.StringIO()
            export_file(file=exported_file, format="application/rdf+xml")
            exported_file.seek(0)
        with Session() as session:
            exported_objects = import_file(
                exported_file, format="application/rdf+xml"
            )
            self.data_integrity(session, exported_objects, label="export")

    def test_application_rdf_xml_guess_format(self):
        """Test guessing and importing the `application/rdf+xml` mime type."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.owl"
            )
            loaded_objects = import_file(test_data_path)
            self.data_integrity(session, loaded_objects, label="import")

    def test_text_turtle(self):
        """Test importing and exporting the `text/turtle` mime type."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.ttl"
            )
            loaded_objects = import_file(test_data_path, format="text/turtle")
            self.data_integrity(session, loaded_objects, label="import")
            exported_file = io.StringIO()
            export_file(file=exported_file, format="text/turtle")
            exported_file.seek(0)
        with Session() as session:
            exported_objects = import_file(exported_file, format="text/turtle")
            self.data_integrity(session, exported_objects, label="export")

    def test_text_turtle_guess_format(self):
        """Test guessing and importing the `text/turtle` mime type."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.ttl"
            )
            loaded_objects = import_file(test_data_path)
            self.data_integrity(session, loaded_objects, label="import")

    def test_application_json(self):
        """Test importing and exporting the `application/ld+json` mime type."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.json"
            )
            loaded_objects = import_file(
                test_data_path, format="application/ld+json"
            )
            self.data_integrity(session, loaded_objects, label="import")
            exported_file = io.StringIO()
            export_file(file=exported_file, format="application/ld+json")
            exported_file.seek(0)
            exported_file.seek(0)
        with Session() as session:
            exported_objects = import_file(
                exported_file, format="application/ld+json"
            )
            self.data_integrity(session, exported_objects, label="export")

    def test_application_json_guess_format(self):
        """Test guessing and importing the `application/ld+json` mime type."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.json"
            )
            loaded_objects = import_file(test_data_path)
            self.data_integrity(session, loaded_objects, label="import")

    def test_application_json_doc_city(self):
        """Test importing the `application/ld+json` mime type from doc dict.

        This test uses a city ontology instead.
        """
        from simphony_osp.namespaces import city

        # Importing
        test_data_path = str(
            Path(__file__).parent / "test_api_importexport_city_import.json"
        )
        with open(test_data_path, "r") as file:
            json_doc = json.loads(file.read())
        with Session() as session:
            loaded_individual = import_file(
                json_doc, format="application/ld+json"
            )
            self.assertTrue(loaded_individual.is_a(city.Citizen))
            self.assertEqual(loaded_individual.name, "Peter")
            self.assertEqual(loaded_individual.age, 23)
            file_io = io.StringIO()
            export_file(
                session,
                file=file_io,
                format="application/ld+json",
                main=loaded_individual,
            )
            file_io.seek(0)
            self.assertTrue(
                self.json_ld_equal(json_doc, json.loads(file_io.read()))
            )

        # Exporting
        test_data_path = str(
            Path(__file__).parent / "test_api_importexport_city_export.json"
        )
        with open(test_data_path, "r") as file:
            json_doc = json.loads(file.read())
        with Session() as session:
            c = branch(
                city.City(name="Freiburg", coordinates=[0, 0], identifier=1),
                city.Neighborhood(
                    name="Littenweiler", coordinates=[0, 0], identifier=2
                ),
                city.Street(
                    name="Schwarzwaldstraße", coordinates=[0, 0], identifier=3
                ),
                rel=city.hasPart,
            )
            file_io = io.StringIO()
            export_file(
                session, file=file_io, format="application/ld+json", main=c
            )
            file_io.seek(0)
            self.assertTrue(
                self.json_ld_equal(json.loads(file_io.read()), json_doc)
            )

    def test_text_turtle_individual_triples(self):
        """Test exporting ontology individual with `text/turtle` mime type.

        This test uses the city ontology.
        """
        from simphony_osp.namespaces import city

        # Exporting
        c = city.City(name="Freiburg", coordinates=[47, 7])
        p1 = city.Citizen(name="Peter", age=25)
        p2 = city.Citizen(name="Anne", age=25)
        c.connect(p1, rel=city.hasInhabitant)
        c.connect(p2, rel=city.hasInhabitant)
        exported_file = io.StringIO()
        export_file(c, file=exported_file, format="text/turtle")
        exported_file.seek(0)
        individual = import_file(exported_file, format="text/turtle")
        self.assertIsInstance(individual, OntologyIndividual)

    def test_text_turtle_file_handle(self):
        """Test importing the `text/turtle` mime type from a file handle."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.ttl"
            )
            with open(test_data_path, "r") as test_data_file:
                loaded_objects = import_file(
                    test_data_file, format="text/turtle"
                )
                self.data_integrity(session, loaded_objects, label="import")

    def test_text_turtle_file_stringio(self):
        """Test importing the `text/turtle` mime type from a file-like."""
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.ttl"
            )
            with open(test_data_path, "r") as test_data_file:
                test_data = test_data_file.read()
            test_data = io.StringIO(test_data)
            loaded_objects = import_file(test_data, format="text/turtle")
            self.data_integrity(session, loaded_objects, label="import")

    def test_text_turtle_another_session(self):
        """Test to a non-default session."""
        another_session = Session()
        with Session() as session:
            test_data_path = str(
                Path(__file__).parent / "test_api_importexport_data.ttl"
            )
            with open(test_data_path, "r") as test_data_file:
                test_data = test_data_file.read()
            test_data = io.StringIO(test_data)
            loaded_objects = import_file(
                test_data, format="text/turtle", session=another_session
            )
            # The expected objects will not be found in session, they will
            # be none.
            for i in range(1, 5):
                self.assertRaises(
                    KeyError,
                    session.from_identifier,
                    URIRef(f"http://example.org/test-ontology#x_{i}"),
                )

            # Test correctness in the other session.
            self.data_integrity(
                another_session, loaded_objects, label="import"
            )

    def test_option_all_triples(self):
        """Tests using the `all_triples` option."""
        from simphony_osp.tools import import_file

        rdf = self.graph_unsupported_triples
        rdf = rdf.serialize(format="turtle", encoding="utf-8").decode("utf-8")

        # Test import: `all_triples=False`.
        file_like = io.StringIO(rdf)
        with Session():
            self.assertRaises(
                RuntimeError,
                import_file,
                file_like,
                format="turtle",
                all_triples=False,
            )

        # Test import: `all_triples=True`.
        file_like = io.StringIO(rdf)
        with Session() as session:
            import_file(file_like, format="turtle", all_triples=True)
            self.assertEqual(1, len(session))
            self.assertEqual(3, len(session.get().one().triples))
            self.assertEqual(3, len(session.graph))

        # Test export: `all_triples=False`.
        file_like = io.StringIO(rdf)
        with Session() as session:
            import_file(file_like, format="turtle", all_triples=True)
            self.assertRaises(
                RuntimeError,
                export_file,
                session,
                format="turtle",
                all_triples=False,
            )

        # Test export: `all_triples=True`.
        file_like = io.StringIO(rdf)
        with Session() as session:
            import_file(file_like, format="turtle", all_triples=True)
            exported = export_file(session, format="turtle", all_triples=True)
            exported = io.StringIO(exported)
        with Session() as session:
            import_file(exported, format="turtle", all_triples=True)
            self.assertEqual(1, len(session))
            self.assertEqual(3, len(session.get().one().triples))
            self.assertEqual(3, len(session.graph))

    def test_option_all_statements(self):
        """Tests using the `all_statements` option."""
        from simphony_osp.tools import import_file

        rdf = self.graph_unsupported_triples
        rdf = rdf.serialize(format="turtle", encoding="utf-8").decode("utf-8")

        # Test import: `all_statements=False`.
        file_like = io.StringIO(rdf)
        with Session():
            self.assertRaises(
                RuntimeError,
                import_file,
                file_like,
                format="turtle",
                all_statements=False
            )

        # Test import: `all_statements=True`.
        file_like = io.StringIO(rdf)
        with Session() as session:
            import_file(file_like, format="turtle", all_statements=True)
            self.assertEqual(1, len(session))
            self.assertEqual(3, len(session.get().one().triples))
            self.assertEqual(4, len(session.graph))

        # Test export: `all_statements=False`.
        file_like = io.StringIO(rdf)
        with Session() as session:
            import_file(file_like, format="turtle", all_statements=True)
            self.assertRaises(
                RuntimeError,
                export_file,
                session,
                format="turtle",
                all_statements=False,
            )

        # Test export: `all_statements=True`.
        file_like = io.StringIO(rdf)
        with Session() as session:
            import_file(file_like, format="turtle", all_statements=True)
            exported = export_file(
                session, format="turtle", all_statements=True
            )
            exported = io.StringIO(exported)
        with Session() as session:
            import_file(exported, format="turtle", all_statements=True)
            self.assertEqual(1, len(session))
            self.assertEqual(3, len(session.get().one().triples))
            self.assertEqual(4, len(session.graph))

    def data_integrity(
        self,
        session: Session,
        loaded_objects: Union[
            OntologyIndividual, Iterable[OntologyIndividual]
        ],
        label: Optional[str] = None,
    ):
        """Checks that the data was loaded correctly into a session.

        Args:
            session: the session where the imported objects have been
                loaded.
            loaded_objects: a list with the loaded ontology individuals.
            label: a label for the subtests (for example 'import' or
                'export'). Makes distinguishing the different integrity checks
                done during a test easier.
        """
        from simphony_osp.namespaces import owl, test_importexport

        if label:
            label = f"({str(label)}) "
        else:
            label = ""

        if isinstance(loaded_objects, OntologyIndividual):
            loaded_objects = {OntologyIndividual}

        # Load the expected objects from their URI, as an incorrect
        # number of them may be loaded when calling import_file.
        expected_objects = tuple(
            session.from_identifier(
                URIRef(f"http://example.org/test-ontology#x_{i}")
            )
            for i in range(1, 5)
        )
        # Each individual in the file
        # represents a "Block" placed in a line. Therefore they may be
        # called object[1], object[2], object[3] and object[4].
        object = {i: obj for i, obj in enumerate(expected_objects, 1)}

        # Test number of loaded ontology individuals.
        with self.subTest(
            msg=f"{label}"
            f"Tests whether the number of loaded ontology individuals "
            "objects is the expected one."
            "\n"
            "Each individual has its x value assigned to "
            "the owl:DataTypeProperty 'x'."
        ):
            self.assertEqual(4, len(loaded_objects))

        # Test attributes.
        with self.subTest(
            msg=f"{label}"
            f"Tests whether attributes are correctly "
            "retrieved."
            "\n"
            "Each individual has its x value assigned to "
            "the owl:DataTypeProperty 'x'."
        ):
            for index, individual in object.items():
                self.assertEqual(getattr(individual, "x"), index)

        # Test classes.
        with self.subTest(
            msg=f"{label}"
            "Tests that the loaded ontology individuals belong to "
            "the correct classes."
        ):
            # Blocks 1, 2 and 4 are named individuals, blocks and forests.
            expected_classes = (
                owl.NamedIndividual,
                test_importexport.Block,
                test_importexport.Forest,
            )
            loaded_classes_for_object = tuple(
                object[i].classes for i in range(1, 2, 4)
            )

            self.sub_test_classes(
                expected_classes, loaded_classes_for_object, label=label
            )

            # Block 3 is a named individual, a block and water.
            expected_classes = (
                owl.NamedIndividual,
                test_importexport.Block,
                test_importexport.Water,
            )
            loaded_classes_for_object = (object[3].classes,)

            self.sub_test_classes(
                expected_classes, loaded_classes_for_object, label=label
            )

        # Test relationships.
        with self.subTest(
            msg=f"{str(label)}"
            "Checks the loaded relationships between ontology individuals "
            "objects."
        ):
            for i in range(1, 4):
                individual = object[i]
                neighbor = individual.get(rel=test_importexport.isLeftOf).one()
                self.assertEqual(neighbor, object[i + 1])
                neighbor = individual.get(rel=test_importexport.isNextTo).one()
                self.assertEqual(neighbor, object[i + 1])

    def sub_test_classes(
        self,
        expected_classes: Tuple[Type, ...],
        loaded_classes_for_object: Tuple[Iterable[Type], ...],
        label: Optional[str] = None,
    ):
        """Compares items on a tuple of expected classes with loaded classes.

        Args:
            expected_classes: A tuple wit the expected
                classes, in any ordering.
            loaded_classes_for_object: Each
                element of the tuple is an iterable representing an ontology
                entity, and each iterable yields the ontology classes of such
                entity.
            label: a label for the subtests (for example 'import' or
                'export'). Makes distinguishing the different integrity checks
                done during a test easier.
        """
        if label:
            label = f"({str(label)}) "
        else:
            label = ""

        # Test equality of classes (hashes).
        expected_names = tuple(cls.__str__() for cls in expected_classes)
        with self.subTest(
            msg=f"{label}"
            f"Testing that the classes of the individuals "
            f'({", ".join(expected_names)}) '
            f"coincide with the expectation (by hash)."
        ):
            for loaded_classes in loaded_classes_for_object:
                self.assertSetEqual(set(expected_classes), set(loaded_classes))

    def json_ld_equal(self, a, b):
        """Check if to JSON documents containing JSON LD are equal."""
        if (
            a
            and isinstance(a, list)
            and isinstance(a[0], dict)
            and "@id" in a[0]
        ) or (a and isinstance(a, dict) and "@graph" in a):
            return isomorphic(json_to_rdf(a, Graph()), json_to_rdf(b, Graph()))
        elif (
            a
            and isinstance(a, list)
            and isinstance(a[0], list)
            and isinstance(a[0][0], dict)
            and "@id" in a[0][0]
        ) or (
            a
            and isinstance(a, list)
            and isinstance(a[0], dict)
            and "@graph" in a[0]
        ):
            graph_a, graph_b = Graph(), Graph()
            for x in a:
                json_to_rdf(x, graph_a)
            for x in b:
                json_to_rdf(x, graph_b)
            return isomorphic(graph_a, graph_b)
        elif (
            isinstance(a, dict)
            and isinstance(b, dict)
            and a.keys() == b.keys()
        ):
            return all(self.json_ld_equal(a[k], b[k]) for k in a.keys())
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            return all(self.json_ld_equal(aa, bb) for aa, bb in zip(a, b))
        else:
            return a == b

    @property
    def graph_unsupported_triples(self) -> Graph:
        """Returns a graph that cannot be fully interpreted by SimPhoNy.

        It includes:
        - An individual that has triples that cannot be understood by SimPhoNy.
        - Triples that do not even belong to a specific individual.

        This method is meant ot be used by the following tests:
        - test_option_all_triples
        - test_option_all_statements
        """
        graph = Graph()
        graph.add(
            (
                URIRef("http://example.org/individuals#1"),
                RDF.type,
                OWL.Thing,
            )
        )
        graph.add(
            (
                URIRef("http://example.org/individuals#1"),
                URIRef("http://example.org/no_meaning#1"),
                URIRef("http://example.org/no_meaning#2"),
            )
        )
        graph.add(
            (
                URIRef("http://example.org/individuals#1"),
                URIRef("http://example.org/no_meaning#3"),
                Literal(
                    58, datatype=URIRef("http://example.org/no_meaning#4")
                ),
            )
        )
        graph.add(
            (
                Literal(18, datatype=XSD.integer),
                URIRef("http://example.org/some_uri"),
                OWL.Thing,
            )
        )
        return graph


class TestToolsSearch(unittest.TestCase):
    """Test the tools related to usage of SimPhoNy over the network.

    Since such tools are more closely related to wrappers, they are actually
    tested in `test_wrapper.py`. This is just a placeholder.
    """

    ontology: Session
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and FOAF.
        """
        cls.ontology = Session(identifier="test-tbox", ontology=True)
        cls.ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.default_ontology
        Session.default_ontology = cls.ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.default_ontology = cls.prev_default_ontology

    def test_find(self):
        """Tests the `find` method."""
        from simphony_osp.namespaces import city
        from simphony_osp.tools import find

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        pr = city.City(name="Paris", coordinates=[0, 1])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        lukas = city.Citizen(name="Lukas", age=3)
        ahmed = city.Citizen(name="Ahmed", age=30)

        fr[city.hasInhabitant] += {marc, sveta, lukas}
        sveta[city.hasChild] += lukas
        marc[city.hasChild] += lukas
        fr[city.hasWorker] += ahmed

        pr[city.hasInhabitant] += ahmed
        pr[city.hasWorker] += ahmed

        self.assertSetEqual(
            {fr, marc, sveta, lukas, ahmed}, set(find(fr, find_all=True))
        )
        self.assertSetEqual(
            {fr, sveta, marc, lukas},
            set(find(fr, rel=city.hasInhabitant, find_all=True)),
        )
        self.assertSetEqual(
            {fr, ahmed}, set(find(fr, rel=city.hasPart, find_all=True))
        )
        self.assertSetEqual(
            {fr, ahmed}, set(find(fr, rel=city.hasWorker, find_all=True))
        )
        self.assertSetEqual(
            {fr, sveta, marc, lukas, ahmed},
            set(
                find(
                    fr, rel={city.hasWorker, city.hasInhabitant}, find_all=True
                )
            ),
        )
        self.assertIn(
            find(fr, rel={city.hasWorker, city.hasInhabitant}, find_all=False),
            {fr, marc, sveta, lukas, ahmed},
        )
        self.assertSetEqual(
            {fr}, set(find(fr, rel=city.hasMajor, find_all=True))
        )
        self.assertEqual(fr, find(fr, rel=city.hasMajor, find_all=False))

        self.assertSetEqual(
            set(), set(find(fr, lambda x: False, find_all=True))
        )
        self.assertIsNone(find(fr, lambda x: False, find_all=False))
        self.assertSetEqual(set(), set(find(fr, lambda x: False)))

        self.assertSetEqual(
            {marc, sveta}, set(find(fr, lambda x: 25 in x[city.age]))
        )
        self.assertIsNone(find(fr, lambda x: 5 in x[city.age], find_all=False))

        fr[city.hasInhabitant] -= lukas
        self.assertSetEqual({fr, sveta, marc, lukas, ahmed}, set(find(fr)))
        self.assertSetEqual(
            {fr, sveta, marc, ahmed}, set(find(fr, max_depth=1))
        )

    def test_find_by_class(self):
        """Tests the `find_by_class` method."""
        from simphony_osp.namespaces import city
        from simphony_osp.tools import find_by_class

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        pr = city.City(name="Paris", coordinates=[0, 1])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        lukas = city.Citizen(name="Lukas", age=3)
        ahmed = city.Citizen(name="Ahmed", age=30)

        fr[city.hasInhabitant] += {marc, sveta, lukas}
        sveta[city.hasChild] += lukas
        marc[city.hasChild] += lukas
        fr[city.hasWorker] += ahmed

        pr[city.hasInhabitant] += ahmed
        pr[city.hasWorker] += ahmed

        self.assertSetEqual(
            {marc, ahmed, sveta, lukas}, set(find_by_class(fr, city.Citizen))
        )

    def test_find_by_attribute(self):
        """Tests the `find_by_attribute` method."""
        from simphony_osp.namespaces import city
        from simphony_osp.tools import find_by_attribute

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        pr = city.City(name="Paris", coordinates=[0, 1])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        lukas = city.Citizen(name="Lukas", age=3)
        ahmed = city.Citizen(name="Ahmed", age=30)

        fr[city.hasInhabitant] += {marc, sveta, lukas}
        sveta[city.hasChild] += lukas
        marc[city.hasChild] += lukas
        fr[city.hasWorker] += ahmed

        pr[city.hasInhabitant] += ahmed
        pr[city.hasWorker] += ahmed

        self.assertSetEqual(
            {marc, sveta},
            set(
                find_by_attribute(
                    fr,
                    city.age,
                    25,
                )
            ),
        )

    def test_find_relationships(self):
        """Tests the `find_relationships` method."""
        from simphony_osp.namespaces import city
        from simphony_osp.tools import find_relationships

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        pr = city.City(name="Paris", coordinates=[0, 1])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        lukas = city.Citizen(name="Lukas", age=3)
        ahmed = city.Citizen(name="Ahmed", age=30)

        fr[city.hasInhabitant] += {marc, sveta, lukas}
        sveta[city.hasChild] += lukas
        marc[city.hasChild] += lukas
        fr[city.hasWorker] += ahmed

        pr[city.hasInhabitant] += ahmed
        pr[city.hasWorker] += ahmed

        self.assertSetEqual(
            {marc, sveta}, set(find_relationships(fr, city.hasChild))
        )

    def test_sparql(self):
        """Tests the `sparql` method."""
        from simphony_osp.namespaces import city
        from simphony_osp.session import core_session
        from simphony_osp.tools import sparql

        core_session.clear()

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        pr = city.City(name="Paris", coordinates=[0, 1])
        marc = city.Citizen(name="Marc", age=25)
        sveta = city.Citizen(name="Sveta", age=25)
        lukas = city.Citizen(name="Lukas", age=3)
        ahmed = city.Citizen(name="Ahmed", age=30)

        fr[city.hasInhabitant] += {marc, sveta, lukas}
        sveta[city.hasChild] += lukas
        marc[city.hasChild] += lukas
        fr[city.hasWorker] += ahmed

        pr[city.hasInhabitant] += ahmed
        pr[city.hasWorker] += ahmed

        persons = set(
            row[0]
            for row in sparql(
                f"""
                SELECT ?person WHERE {{
                    ?person rdf:type <{city.Citizen.iri}> .
                }}
            """
            )(person=OntologyIndividual)
        )
        self.assertSetEqual({marc, sveta, lukas, ahmed}, persons)

        with Session():
            persons = set(
                row[0]
                for row in sparql(
                    f"""
                    SELECT ?person WHERE {{
                        ?person rdf:type <{city.Citizen.iri}> .
                    }}
                """
                )(person=OntologyIndividual)
            )
            self.assertSetEqual(set(), persons)


if __name__ == "__main__":
    unittest.main()
