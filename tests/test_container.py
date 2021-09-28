"""Test the container architecture."""

import unittest

from rdflib import URIRef

from osp.core.ontology.parser.owl.parser import OWLParser
from osp.core.ontology.parser.yml.parser import YMLParser
from osp.core.session.session import Session


class TestContainer(unittest.TestCase):
    """Tests the containers."""

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox containing CUBA, OWL and City."""
        ontology = Session(identifier='test-tbox', ontology=True)
        for parser in (OWLParser('cuba'), OWLParser('owl'), YMLParser('city')):
            ontology.load_parser(parser)
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def test_container_general(self):
        """Temporary test while development is ongoing."""
        # TODO: remove this test once development is complete. Possibly by
        #  splitting it into smaller test, and above all, using the end-user
        #  interface to create containers.
        from osp.core.ontology.interactive.container import Container
        from osp.core.ontology.datatypes import UID
        city = Session.ontology.get_namespace('city')

        container = Container(uid=UID())

        self.assertIsNone(container.opens_in)
        self.assertIsNone(container.session_linked)
        self.assertFalse(container.is_open)
        self.assertSetEqual(set(), set(container.references))
        self.assertEqual(len(container.references), 0)
        self.assertEqual(container.num_references, 0)

        with container:
            self.assertIs(Session.default_session, container.session_linked)
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

        another_container = Container(uid=UID())

        another_container.opens_in = container
        self.assertRaises(RuntimeError, another_container.open)
        container.open()
        with another_container:
            self.assertIs(Session.default_session, container.session_linked)
            self.assertIs(container.session_linked,
                          another_container.session_linked)
        container.close()

        fr_session = Session()
        fr = city.City(name='Freiburg', session=fr_session)
        container.references = {fr.iri}
        default_session = Session.default_session

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
