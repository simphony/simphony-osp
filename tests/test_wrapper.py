"""Tests the wrapper as user-facing session management interface."""

import os
import unittest

from osp.core.ontology.datatypes import Vector
from osp.core.ontology.parser.owl.parser import OWLParser
from osp.core.ontology.parser.yml.parser import YMLParser
from osp.core.session.session import Session


class TestWrapper(unittest.TestCase):
    """Test the full end-user experience of using wrapper.

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

    def test_wrapper_city(self) -> None:
        """Test adding some entities from the city ontology."""
        from osp.core.namespaces import city
        from osp.wrappers import sqlite

        with sqlite(self.file_name) as wrapper:
            freiburg = city.City(name='Freiburg', coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(iri='http://example.org/citizens#Marco',
                                 name='Marco',
                                 age=50)
            matthias = city.Citizen(name='Matthias', age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            self.assertIn(marco, set(wrapper))
            self.assertIn(matthias, set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual({marco, matthias, freiburg}, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            self.assertEqual(freiburg.name, 'Freiburg')
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, 'Marco')
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, 'Matthias')
            self.assertEqual(matthias.age, 37)
            wrapper.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with sqlite(self.file_name) as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            citizens = list(freiburg[city.hasInhabitant, :])

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

            everything = {*citizens, freiburg}
            self.assertIn(citizens[0], set(wrapper))
            self.assertIn(citizens[1], set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual(everything, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            wrapper.delete(*citizens)
            self.assertEqual(len(wrapper), 1)
            self.assertEqual(len(freiburg[city.hasInhabitant, :]), 0)

            wrapper.delete(freiburg)
            self.assertEqual(len(wrapper), 0)

            wrapper.commit()

        pr = city.City(name='Paris')

        with sqlite(self.file_name) as wrapper:
            self.assertEqual(len(wrapper), 0)
            wrapper.add(pr)
            wrapper.commit()

        with sqlite(self.file_name) as wrapper:
            self.assertEqual(len(wrapper), 1)
            paris = set(wrapper).pop()
            self.assertEqual(paris.name, 'Paris')

    def test_wrapper_root(self) -> None:
        """Test using an ontology entity as wrapper."""
        from osp.core.namespaces import city
        from osp.wrappers import sqlite

        fr = city.City(iri='http://example.org/Freiburg', name='Freiburg')

        with sqlite(self.file_name, root=fr) as freiburg_as_wrapper_1:
            marco = city.Citizen(iri='http://example.org/citizens#Marco',
                                 name='Marco',
                                 age=50)
            matthias = city.Citizen(name='Matthias', age=37)

            freiburg_as_wrapper_1[city.hasInhabitant, :] = {marco, matthias}

            freiburg_as_wrapper_1.commit()

        with sqlite(self.file_name, root='http://example.org/Freiburg') \
                as freiburg_as_wrapper_2:
            citizens = list(freiburg_as_wrapper_2[city.hasInhabitant, :])

            self.assertEqual('Freiburg', freiburg_as_wrapper_2.name)
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
