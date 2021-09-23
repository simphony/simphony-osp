import tempfile
import unittest
import os
from typing import Optional, TYPE_CHECKING

from rdflib import RDF, URIRef, Graph

from osp.core.namespaces import cuba
from osp.core.ontology.datatypes import UID, Vector
from osp.core.ontology.individual import OntologyIndividual
from osp.core.ontology.parser.owl.parser import OWLParser
from osp.core.ontology.parser.yml.parser import YMLParser
from osp.core.session.interfaces.interface import Interface, InterfaceStore
from osp.core.session.interfaces.sql import SQLStore
from osp.core.session.session import Session
from osp.interfaces.sqlite.interface import SQLiteInterface
from osp.wrappers import sqlite

if TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity


class TestDummyInterface(unittest.TestCase):
    """Test that the RDFLib store interface works as expected."""

    graph: Graph

    DummyStore = InterfaceStore

    class DummyInterface(Interface):

        def __init__(self):
            super().__init__()
            self._graph = Graph()

        def __str__(self):
            return "Dummy interface"

        def apply_added(self, entity: "OntologyEntity") -> None:
            for triple in entity.triples:
                self._graph.add(triple)

        def apply_updated(self, entity: "OntologyEntity") -> None:
            self._graph.remove((entity.identifier, None, None))
            for triple in entity.triples:
                self._graph.add(triple)

        def apply_deleted(self, entity: "OntologyEntity") -> None:
            self._graph.remove((entity.identifier, None, None))

        def _load_from_backend(self, uid: UID) -> \
                Optional["OntologyIndividual"]:
            triples = set(self._graph.triples(
                (uid.to_identifier(), None, None)))
            if triples:
                return OntologyIndividual(
                    uid=uid,
                    extra_triples=triples)
            else:
                return None

        def open(self, configuration: str):
            pass

        def close(self):
            pass

    def setUp(self) -> None:
        """Create an interface, a store and assign them to a session."""
        interface = self.DummyInterface()
        store = self.DummyStore(interface=interface)
        self.graph = Graph(store)

    def test_buffered(self):
        """Tests the store without committing the changes."""

        self.assertTrue(isinstance(self.graph.store, self.DummyStore))
        self.assertRaises(NotImplementedError,
                          lambda x: set(self.graph.triples(x)),
                          (None, None, None))

        # Add triples from a cuba entity to the store.
        entity = cuba.Entity()
        self.assertTrue(entity.is_a(cuba.Entity))

        for triple in entity.triples:
            self.graph.add(triple)
        self.assertSetEqual(
            {(entity.identifier, RDF.type, cuba.Entity.identifier)},
            set(self.graph.triples(
                (entity.identifier, None, None))))

        # Remove triples from a cuba entity from the store.
        for triple in entity.triples:
            self.graph.remove(triple)
        self.assertSetEqual(set(),
                            set(self.graph.triples(
                                (entity.identifier, None, None))))

        # Add triples to an existing entity in the store.
        for triple in entity.triples:
            self.graph.add(triple)
        self.graph.add(
            (entity.identifier, URIRef("some:predicate"),
             URIRef("some:object")))
        self.assertSetEqual(
            {(entity.identifier, RDF.type, cuba.Entity.identifier),
             (entity.identifier, URIRef("some:predicate"),
              URIRef("some:object"))},
            set(self.graph.triples(
                (entity.identifier, None, None))))

    def test_commit(self):
        """Tests the store committing the changes."""

        # Add triples from a cuba entity to the store.
        entity = cuba.Entity()
        self.assertTrue(entity.is_a(cuba.Entity))

        for triple in entity.triples:
            self.graph.add(triple)
        self.graph.commit()
        self.assertSetEqual(
            {(entity.identifier, RDF.type, cuba.Entity.identifier)},
            set(self.graph.triples(
                (entity.identifier, None, None))))

        # Remove triples from a cuba entity from the store.
        for triple in entity.triples:
            self.graph.remove(triple)
        self.graph.commit()
        self.assertSetEqual(set(),
                            set(self.graph.triples(
                                (entity.identifier, None, None))))

        # Update an entity in the store.
        for triple in entity.triples:
            self.graph.add(triple)
        self.graph.commit()
        self.graph.add(
            (entity.identifier, URIRef("some:predicate"),
             URIRef("some:object")))
        self.graph.commit()
        self.assertSetEqual(
            {(entity.identifier, RDF.type, cuba.Entity.identifier),
             (entity.identifier, URIRef("some:predicate"),
              URIRef("some:object"))},
            set(self.graph.triples(
                (entity.identifier, None, None))))


class TestTriplestoreInterface(unittest.TestCase):

    file_name: str = "TestSQLiteInterface"

    graph: Graph

    FOAF: str = """
    format: xml
    identifier: foaf
    namespaces:
      foaf: http://xmlns.com/foaf/0.1/
    ontology_file: http://xmlns.com/foaf/spec/index.rdf
    reference_by_label: false
    """

    def setUp(self) -> None:
        """Create an interface, a store and assign them to a session."""
        self.interface = SQLiteInterface(self.file_name)
        self.store = SQLStore(interface=self.interface)
        self.graph = Graph(self.store)

        # Use FOAF ontology as example.
        with tempfile.NamedTemporaryFile('w', suffix='.yml', delete=False) \
                as file:
            self.yml_path = file.name
            file.write(self.FOAF)
            file.seek(0)
        foaf_parser = OWLParser(self.yml_path)
        self.ontology = Session(from_parser=foaf_parser,
                                ontology=True)
        self.foaf = self.ontology.get_namespace("foaf")

    def tearDown(self) -> None:
        try:
            self.interface.close()
            os.remove(self.file_name)
        except FileNotFoundError:
            pass

    def test_basic(self):
        """Tests basic functionality."""
        self.assertTrue(os.path.exists(self.file_name))

        person = self.foaf['Person']()

        # Test add.
        for triple in person.triples:
            self.graph.add(triple)
        self.assertSetEqual(set(person.triples),
                            set(self.graph.triples((None, None, None))))

        # Test remove.
        for triple in person.triples:
            self.graph.remove(triple)
        self.assertSetEqual(set(),
                            set(self.graph.triples((None, None, None))))

    def test_retrieval(self):

        self.assertTrue(os.path.exists(self.file_name))

        person = self.foaf['Person']()

        # Add some triples, commit and close the store.
        for triple in person.triples:
            self.graph.add(triple)
        self.assertSetEqual(set(person.triples),
                            set(self.graph.triples((None, None, None))))
        self.graph.commit()
        self.graph.close()

        # Use a new interface to reopen the file and retrieve the data.
        interface = SQLiteInterface(self.file_name)
        store = SQLStore(interface=interface)
        graph = Graph(store)
        self.assertSetEqual(set(person.triples),
                            set(graph.triples((None, None, None))))

        # Delete the triples, commit and close the connection.
        graph.remove((None, None, None))
        graph.commit()
        graph.close()

        # Again reopen in a new interface and check that the commit went well.
        interface = SQLiteInterface(self.file_name)
        store = SQLStore(interface=interface)
        graph = Graph(store)
        self.assertSetEqual(set(),
                            set(graph.triples((None, None, None))))


class TestTriplestoreWrapper(unittest.TestCase):

    file_name: str = "TestSQLiteSession"

    def setUp(self) -> None:
        """Create an interface, a store and assign them to a session."""
        self.ontology = Session(identifier='test_tbox',
                                ontology=True)
        cuba_parser = OWLParser('cuba')
        self.ontology.load_parser(cuba_parser)
        owl_parser = OWLParser('owl')
        self.ontology.load_parser(owl_parser)
        city_parser = YMLParser('city')
        self.ontology.load_parser(city_parser)
        self.city = self.ontology.get_namespace('city')

    def tearDown(self) -> None:
        try:
            os.remove(self.file_name)
        except FileNotFoundError:
            pass

    def test_city(self) -> None:

        with sqlite(self.file_name, ontology=self.ontology) as session:
            freiburg = self.city.City(name='Freiburg', coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = self.city.Citizen(name='Marco', age=50)
            matthias = self.city.Citizen(name='Matthias', age=37)
            freiburg[self.city.hasInhabitant] = {marco, matthias}

            self.assertEqual(freiburg.name, 'Freiburg')
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, 'Marco')
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, 'Matthias')
            self.assertEqual(matthias.age, 37)
            session.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with sqlite(self.file_name, ontology=self.ontology) as session:
            freiburg = session.from_identifier(freiburg_identifier)
            citizens = freiburg[self.city.hasInhabitant, :]

            self.assertEqual('Freiburg', freiburg.name)
            self.assertEqual([20, 58], freiburg.coordinates)
            self.assertSetEqual(
                {'Marco', 'Matthias'},
                {citizen.name for citizen in citizens}
            )
            self.assertSetEqual(
                {50, 37},
                {citizen.age for citizen in citizens}
            )


if __name__ == "__main__":
    unittest.main()
