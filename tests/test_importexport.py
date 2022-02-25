"""Test general RDF data import."""

import io
import unittest
import json
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.compare import isomorphic
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf

from simphony_osp.core.ontology.individual import OntologyIndividual
from simphony_osp.core.ontology.parser import OntologyParser
from simphony_osp.core.session import Session
from simphony_osp.core.utils.general import import_cuds, export_cuds, branch

# Load the ontology for the test.
try:
    from simphony_osp.namespaces import test_importexport
except ImportError:  # If the ontology is not installed.
    Session.ontology.load_parser(OntologyParser.get_parser(
        str(Path(__file__).parent / "test_importexport.owl.yml")))
    test_importexport = Session.ontology.get_namespace('test_importexport')

# Load also the city ontology.
try:
    from simphony_osp.namespaces import city
except ImportError:  # When the city ontology is not installed.
    Session.ontology.load_parser(OntologyParser.get_parser('city'))
    city = Session.ontology.get_namespace('city')


def json_ld_equal(a, b):
    """Check if to JSON documents containing JSON LD are equal."""
    if (
        a and isinstance(a, list) and isinstance(a[0], dict)
            and "@id" in a[0]
    ) or (
        a and isinstance(a, dict) and "@graph" in a
    ):
        return isomorphic(json_to_rdf(a, Graph()),
                          json_to_rdf(b, Graph()))
    elif (
        a and isinstance(a, list) and isinstance(a[0], list)
            and isinstance(a[0][0], dict) and "@id" in a[0][0]
    ) or (
        a and isinstance(a, list) and isinstance(a[0], dict)
            and "@graph" in a[0]
    ):
        graph_a, graph_b = Graph(), Graph()
        for x in a:
            json_to_rdf(x, graph_a)
        for x in b:
            json_to_rdf(x, graph_b)
        return isomorphic(graph_a, graph_b)
    elif isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return all(json_ld_equal(a[k], b[k]) for k in a.keys())
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return all(json_ld_equal(aa, bb) for aa, bb in zip(a, b))
    else:
        return a == b


class TestImportExport(unittest.TestCase):
    """Loads files containing CUDS and checks the correctness of the data.

    The loading process returns cuds objects corresponding to the individuals
    in the ontology. Some of the known information about the individuals in
    the file is tested against the loaded data.
    """

    def test_application_rdf_xml(self):
        """Test importing and exporting the `application/rdf+xml` mime type."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.owl")
            loaded_objects = import_cuds(test_data_path,
                                         format='application/rdf+xml')
            data_integrity(self, session, loaded_objects, label='import')
            exported_file = io.StringIO()
            export_cuds(file=exported_file, format='application/rdf+xml')
            exported_file.seek(0)
        with Session() as session:
            exported_objects = import_cuds(exported_file,
                                           format='application/rdf+xml')
            data_integrity(self, session, exported_objects, label='export')

    def test_application_rdf_xml_guess_format(self):
        """Test guessing and importing the `application/rdf+xml` mime type."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.owl")
            loaded_objects = import_cuds(test_data_path)
            data_integrity(self, session, loaded_objects, label='import')

    def test_text_turtle(self):
        """Test importing and exporting the `text/turtle` mime type."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.ttl")
            loaded_objects = import_cuds(test_data_path,
                                         format='text/turtle')
            data_integrity(self, session, loaded_objects, label='import')
            exported_file = io.StringIO()
            export_cuds(file=exported_file, format='text/turtle')
            exported_file.seek(0)
        with Session() as session:
            exported_objects = import_cuds(exported_file,
                                           format='text/turtle')
            data_integrity(self, session, exported_objects, label='export')

    def test_text_turtle_guess_format(self):
        """Test guessing and importing the `text/turtle` mime type."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.ttl")
            loaded_objects = import_cuds(test_data_path)
            data_integrity(self, session, loaded_objects, label='import')

    def test_application_json(self):
        """Test importing and exporting the `application/ld+json` mime type."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.json")
            loaded_objects = import_cuds(test_data_path,
                                         format='application/ld+json')
            data_integrity(self, session, loaded_objects, label='import')
            exported_file = io.StringIO()
            export_cuds(file=exported_file, format='application/ld+json')
            exported_file.seek(0)
            exported_file.seek(0)
        with Session() as session:
            exported_objects = import_cuds(exported_file,
                                           format='application/ld+json')
            data_integrity(self, session, exported_objects, label='export')

    def test_application_json_guess_format(self):
        """Test guessing and importing the `application/ld+json` mime type."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.json")
            loaded_objects = import_cuds(test_data_path)
            data_integrity(self, session, loaded_objects, label='import')

    def test_application_json_doc_city(self):
        """Test importing the `application/ld+json` mime type from doc dict.

        This test uses a city ontology instead.
        """
        # Importing
        test_data_path = str(Path(__file__).parent
                             / "test_importexport_city_import.json")
        with open(test_data_path, 'r') as file:
            json_doc = json.loads(file.read())
        with Session():
            cuds = import_cuds(json_doc, format='application/ld+json')
            self.assertTrue(cuds.is_a(city.Citizen))
            self.assertEqual(cuds.name, "Peter")
            self.assertEqual(cuds.age, 23)
            export_file = io.StringIO()
            export_cuds(cuds, file=export_file, format='application/ld+json')
            export_file.seek(0)
            self.assertTrue(json_ld_equal(json_doc,
                                          json.loads(export_file.read())))
        # Exporting
        test_data_path = str(Path(__file__).parent
                             / "test_importexport_city_export.json")
        with open(test_data_path, 'r') as file:
            json_doc = json.loads(file.read())
        with Session():
            c = branch(
                city.City(name="Freiburg",
                          coordinates=[0, 0],
                          uid=1),
                branch(
                    city.Neighborhood(name="Littenweiler",
                                      coordinates=[0, 0],
                                      uid=2),
                    city.Street(name="Schwarzwaldstraße",
                                coordinates=[0, 0],
                                uid=3)
                )
            )
            export_file = io.StringIO()
            export_cuds(c, file=export_file, format='application/ld+json')
            export_file.seek(0)
            self.assertTrue(json_ld_equal(json.loads(export_file.read()),
                                          json_doc))

    def test_text_turtle_cuds_triples(self):
        """Test exporting the `text/turtle` mime type from a cuds object.

        This test uses the city ontology.
        """
        # Exporting
        c = city.City(name="Freiburg", coordinates=[47, 7])
        p1 = city.Citizen(name="Peter", age=25)
        p2 = city.Citizen(name="Anne", age=25)
        c.add(p1, rel=city.hasInhabitant)
        c.add(p2, rel=city.hasInhabitant)
        exported_file = io.StringIO()
        export_cuds(c, file=exported_file, format='text/turtle')
        exported_file.seek(0)
        cuds = import_cuds(exported_file, format='text/turtle')
        self.assertIs(type(cuds), OntologyIndividual)

    def test_text_turtle_file_handle(self):
        """Test importing the `text/turtle` mime type from a file handle."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.ttl")
            with open(test_data_path, 'r') as test_data_file:
                loaded_objects = import_cuds(test_data_file,
                                             format='text/turtle')
                data_integrity(self, session, loaded_objects, label='import')

    def test_text_turtle_file_stringio(self):
        """Test importing the `text/turtle` mime type from a file-like."""
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.ttl")
            with open(test_data_path, 'r') as test_data_file:
                test_data = test_data_file.read()
            test_data = io.StringIO(test_data)
            loaded_objects = import_cuds(test_data,
                                         format='text/turtle')
            data_integrity(self, session, loaded_objects, label='import')

    def test_text_turtle_another_session(self):
        """Test to a non-default session."""
        another_session = Session()
        with Session() as session:
            test_data_path = str(Path(__file__).parent
                                 / "test_importexport_data.ttl")
            with open(test_data_path, 'r') as test_data_file:
                test_data = test_data_file.read()
            test_data = io.StringIO(test_data)
            loaded_objects = import_cuds(test_data,
                                         format='text/turtle',
                                         session=another_session)
            # The expected objects will not be found in session, they will
            # be none.
            for i in range(1, 5):
                self.assertRaises(
                    KeyError, session.from_identifier,
                    URIRef(f'http://example.org/test-ontology#x_{i}'))

            # Test correctness in the other session.
            data_integrity(self, another_session, loaded_objects,
                           label='import')


def data_integrity(testcase, session, loaded_objects, label=None):
    """Checks that the data was loaded correctly into a session.

    Args:
        testcase (unittest.TestCase): the test case where this function is
            being called.
        session (Session): the session where the imported objects have been
            loaded.
        loaded_objects (List[Cuds]): a list with the loaded cuds objects.
        label(str): a label for the subtests (for example 'import' or
            'export'). Makes distinguishing the different integrity checks
            done during a test easier.
    """
    if label:
        label = f'({str(label)}) '
    else:
        label = ''

    # Load the expected objects from their URI, as an incorrect
    # number of them may be loaded when calling import_cuds.
    expected_objects = tuple(session.from_identifier(
        URIRef(f'http://example.org/test-ontology#x_{i}'))
        for i in range(1, 5))
    # Each individual in the file
    # represents a "Block" placed in a line. Therefore they may be
    # called object[1], object[2], object[3] and object[4].
    object = {i: obj for i, obj
              in enumerate(expected_objects, 1)}

    # Test number of loaded CUDS.
    with testcase.subTest(msg=f"{label}"
                              f"Tests whether the number of loaded CUDS "
                              "objects is the expected one."
                              "\n"
                              "Each individual has its x value assigned to "
                              "the owl:DataTypeProperty 'x'."):
        testcase.assertEqual(4, len(loaded_objects))

    # Test attributes.
    with testcase.subTest(msg=f"{label}"
                              f"Tests whether attributes are correctly "
                              "retrieved."
                              "\n"
                              "Each individual has its x value assigned to "
                              "the owl:DataTypeProperty 'x'."):
        for index, cuds in object.items():
            testcase.assertEqual(getattr(cuds, 'x'), index)

    # Test classes.
    with testcase.subTest(msg=f"{label}"
                              "Tests that the loaded CUDS objects belong to "
                              "the correct classes."):
        # Blocks 1, 2 and 4 are both blocks and forests.
        expected_classes = (test_importexport.Block,
                            test_importexport.Forest)
        loaded_classes_for_object = tuple(object[i].oclasses
                                          for i in range(1, 2, 4))

        sub_test_classes(testcase, expected_classes, loaded_classes_for_object,
                         label=label)

        # Block 3 is both a block and water.
        expected_classes = (test_importexport.Block,
                            test_importexport.Water)
        loaded_classes_for_object = (object[3].oclasses,)

        sub_test_classes(testcase, expected_classes, loaded_classes_for_object,
                         label=label)

    # Test relationships.
    with testcase.subTest(msg=f"{str(label)}"
                              "Checks the loaded relationships between CUDS "
                              "objects."):
        for i in range(1, 4):
            cuds = object[i]
            neighbor = cuds.get(rel=test_importexport.isLeftOf).one()
            testcase.assertEqual(neighbor, object[i + 1])
            neighbor = cuds.get(rel=test_importexport.isNextTo).one()
            testcase.assertEqual(neighbor, object[i + 1])


def sub_test_classes(testcase, expected_classes, loaded_classes_for_object,
                     label=None):
    """Compares items on a tuple of expected classes with loaded classes.

    Args:
        testcase (unittest.TestCase): the test case where this function is
            being called.
        expected_classes (Tuple[class, ...]): A tuple wit the expected
            classes, in any ordering.
        loaded_classes_for_object (Tuple[Iterable[class, ...]]): Each
            element of the tuple is an iterable representing an ontology
            entity, and each iterable yields the ontology classes of such
            entity.
        label(str): a label for the subtests (for example 'import' or
            'export'). Makes distinguishing the different integrity checks
            done during a test easier.
    """
    if label:
        label = f'({str(label)}) '
    else:
        label = ''

    # Test equality of classes (hashes).
    expected_names = tuple(cls.__str__() for cls in expected_classes)
    with testcase.subTest(msg=f"{label}"
                              f'Testing that the classes of the individuals '
                              f'({", ".join(expected_names)}) '
                              f'coincide with the expectation (by hash).'):
        for loaded_classes in loaded_classes_for_object:
            testcase.assertSetEqual(set(expected_classes),
                                    set(loaded_classes))


if __name__ == "__main__":
    unittest.main()
