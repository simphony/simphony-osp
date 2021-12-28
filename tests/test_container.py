"""Test the container architecture."""

import unittest

from rdflib import URIRef

from osp.core.ontology.parser import OntologyParser
from osp.core.session.session import Session


class TestContainer(unittest.TestCase):
    """Tests the containers."""

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        ontology = Session(identifier='test-tbox', ontology=True)
        ontology.load_parser(OntologyParser.get_parser('city'))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def test_container(self):
        """Test the container ontology individual."""
        from osp.core.namespaces import city, cuba

        container = cuba.Container()

        self.assertIsNone(container.opens_in)
        self.assertIsNone(container.session_linked)
        self.assertFalse(container.is_open)
        self.assertSetEqual(set(), set(container.references))
        self.assertEqual(len(container.references), 0)
        self.assertEqual(container.num_references, 0)

        with container:
            self.assertIs(Session.get_default_session(),
                          container.session_linked)
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
        self.assertRaises(TypeError,
                          lambda x: setattr(container, 'opens_in', x), 8)
        container.opens_in = None

        another_container = cuba.Container()

        another_container.opens_in = container
        self.assertRaises(RuntimeError, another_container.open)
        container.open()
        with another_container:
            self.assertIs(Session.get_default_session(),
                          container.session_linked)
            self.assertIs(container.session_linked,
                          another_container.session_linked)
        container.close()

        fr_session = Session()
        fr = city.City(name='Freiburg',
                       coordinates=[0, 0],
                       session=fr_session)
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

        broken_reference = URIRef('http://example.org/things#something')
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
                pr = city.City(name='Paris', coordinates=[0, 0])
                self.assertSetEqual({fr, pr}, set(container))

    def test_container_multiple_sessions(self):
        """Test opening the container in different sessions.

        Each session is meant to contain a different version of the same
        individual.
        """
        from osp.core.namespaces import cuba, city

        container = cuba.Container()

        default_session = Session.get_default_session()
        session_1 = Session()
        session_2 = Session()

        klaus = city.Citizen(name='Klaus', age=5)
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


if __name__ == "__main__":
    unittest.main()
