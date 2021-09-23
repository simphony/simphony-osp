"""Test the interface API to communicate with external software."""

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
    """Test that the InterfaceStore RDFLib store works as expected."""

    graph: Graph

    DummyStore = InterfaceStore

    class DummyInterface(Interface):
        """A sample interface (based on an RDFLib Graph.

        It has the sole purpose of being used an interface for testing the
        InterfaceStore.
        """

        def __init__(self):
            """Set up a graph to use as underlying backend."""
            super().__init__()
            self._graph = Graph()

        def apply_added(self, entity: "OntologyEntity") -> None:
            """Convert received entity to triples and add them to the graph."""
            for triple in entity.triples:
                self._graph.add(triple)

        def apply_updated(self, entity: "OntologyEntity") -> None:
            """Update entity in the graph.

            Since all the triples for an entity are received, the update
            consists on removing all the existing triples and adding the
            ones provided by the updated version of the entity.
            """
            self._graph.remove((entity.identifier, None, None))
            for triple in entity.triples:
                self._graph.add(triple)

        def apply_deleted(self, entity: "OntologyEntity") -> None:
            """Remove all triples that have the received entity as subject."""
            self._graph.remove((entity.identifier, None, None))

        def _load_from_backend(self, uid: UID) -> \
                Optional["OntologyIndividual"]:
            """Spawn an ontology individual matching the received uid."""
            triples = set(self._graph.triples(
                (uid.to_identifier(), None, None)))
            if triples:
                return OntologyIndividual(
                    uid=uid,
                    extra_triples=triples)
            else:
                return None

        def open(self, configuration: str):
            """Not needed, but an implementation is expected."""
            pass

        def close(self):
            """Not needed, but an implementation is expected."""
            pass

    def setUp(self) -> None:
        """Create an interface, a store and assign them to a graph."""
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
    """Test an actual TriplestoreInterface, the SQLiteInterface."""

    file_name: str = "TestSQLiteInterface"  # Filename for database file.

    FOAF: str = """
    format: xml
    identifier: foaf
    namespaces:
      foaf: http://xmlns.com/foaf/0.1/
    ontology_file: http://xmlns.com/foaf/spec/index.rdf
    reference_by_label: false
    """

    graph: Graph
    yml_path: str
    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox only containing CUBA and FOAF.

        Such TBox is set as the default TBox.
        """
        with tempfile.NamedTemporaryFile('w', suffix='.yml', delete=False) \
                as file:
            cls.yml_path = file.name
            file.write(cls.FOAF)
            file.seek(0)
        ontology = Session(identifier='test-tbox', ontology=True)
        for parser in (OWLParser('cuba'), OWLParser(cls.yml_path)):
            ontology.load_parser(parser)
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def setUp(self) -> None:
        """Create an interface, a store and assign them to a graph."""
        self.interface = SQLiteInterface(self.file_name)
        self.store = SQLStore(interface=self.interface)
        self.graph = Graph(self.store)

    def tearDown(self) -> None:
        """Remove the database file."""
        try:
            self.interface.close()
            os.remove(self.file_name)
        except FileNotFoundError:
            pass

    def test_basic(self):
        """Tests basic functionality.

        - Adding triples.
        - Removing triples.
        """
        from osp.core.namespaces import foaf
        self.assertTrue(os.path.exists(self.file_name))

        person = foaf['Person']()

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
        """Tests retrieving stored triples from the interface."""
        from osp.core.namespaces import foaf
        self.assertTrue(os.path.exists(self.file_name))

        person = foaf['Person']()

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
    """Test the full end-user experience of using a triplestore wrapper.

    The wrapper used for the test is the `sqlite` wrapper.
    """

    file_name: str = "TestSQLiteSession"

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox with the CUBA, OWL and city ontologies.

        Such TBox is set as the default TBox.
        """
        ontology = Session(identifier='test_tbox', ontology=True)
        for parser in (OWLParser('cuba'),
                       OWLParser('owl'),
                       YMLParser('city')):
            ontology.load_parser(parser)
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def tearDown(self) -> None:
        """Remove the database file."""
        try:
            os.remove(self.file_name)
        except FileNotFoundError:
            pass

    def test_city(self) -> None:
        """Test adding some entities from the city ontology."""
        from osp.core.namespaces import city

        with sqlite(self.file_name) as session:
            freiburg = city.City(name='Freiburg', coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(name='Marco', age=50)
            matthias = city.Citizen(name='Matthias', age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            self.assertEqual(freiburg.name, 'Freiburg')
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, 'Marco')
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, 'Matthias')
            self.assertEqual(matthias.age, 37)
            session.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with sqlite(self.file_name) as session:
            freiburg = session.from_identifier(freiburg_identifier)
            citizens = freiburg[city.hasInhabitant, :]

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
