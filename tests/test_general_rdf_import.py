"""Test general RDF data import."""

import unittest2 as unittest
import rdflib
from osp.core.utils import import_rdf_file


# Load the ontology for the test.
try:
    from osp.core.namespaces import test_general_rdf_import
except ImportError:  # If the ontology is not installed.
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("test_general_rdf_import.owl.yml")
    _namespace_registry.update_namespaces()
    test_general_rdf_import = _namespace_registry.test_general_rdf_import


class TestRDFImport(unittest.TestCase):
    """Loads an RDF file and does checks on the correctness of the loaded data.

    The test loads the file specified by the class attribute below. The process
    returns cuds objects corresponding to the individuals in the ontology. Some
    of the known information about the individuals in the file is tested
    against the loaded data.
    """

    test_ontology_path = './test_general_rdf_import.owl'

    def __init__(self, *args, **kwargs):
        """Loads the RDF file to be used in the test."""
        super().__init__(*args, **kwargs)

        self.loaded_objects = import_rdf_file(self.test_ontology_path,
                                              format='xml')
        self.loaded_objects = list(self.loaded_objects)
        self.session = self.loaded_objects[0].session
        self.graph = self.loaded_objects[0]._graph

        # Load also the expected objects from their URI, as an incorrect
        # number of them may be loaded when calling import_rdf_file.
        self.expected_objects = tuple(self.session.load_from_iri(
            rdflib.URIRef(f'http://example.org/test-ontology#x_{i}')).first()
            for i in range(1, 5))
        # Each individual in the file
        # represents a "Block" placed in a line. Therefore they may be
        # called object[1], onbject[2], object[3] and object[4].
        self.object = {i: obj for i, obj
                       in enumerate(self.expected_objects, 1)}

    def test_number_of_objects_loaded(self):
        """Tests whether the number of loaded CUDS objects is the expected one.

        Exactly four CUDS objects are expected, as there are exactly four
        individuals in the loaded file.
        """
        self.assertEqual(4, len(self.loaded_objects))

    def test_attributes(self):
        """Tests whether attributes are correctly retrieved.

        Each individual has its x value assigned to the
        owl:DataTypeProperty "x".
        """
        for index, cuds in self.object.items():
            self.assertEqual(getattr(cuds, 'x'), index)

    def test_classes(self):
        """Tests that the loaded CUDS objects belong to the correct classes."""
        # Blocks 1, 2 and 4 are both blocks and forests.
        expected_classes = (test_general_rdf_import.Block,
                            test_general_rdf_import.Forest)
        loaded_classes_for_object = tuple(self.object[i].oclasses
                                          for i in range(1, 2, 4))

        self.sub_test_classes(expected_classes, loaded_classes_for_object)

        # Block 3 is both a block and water.
        expected_classes = (test_general_rdf_import.Block,
                            test_general_rdf_import.Water)
        loaded_classes_for_object = (self.object[3].oclasses, )

        self.sub_test_classes(expected_classes, loaded_classes_for_object)

    def sub_test_classes(self, expected_classes, loaded_classes_for_object):
        """Compares a items on a tuple of expected classes with loaded classes.

        Args:
            expected_classes (Tuple[class, ...]): A tuple wit the expected
                                                  classes, in any ordering.
            loaded_classes_for_object (Tuple[Iterable[class, ...]]): Each
                                                  element of the tuple is an
                                                  iterable representing an
                                                  ontology entity, and each
                                                  iterable yields the ontology
                                                  classes of such entity.
        """
        # Test equality of classes (hashes).
        expected_names = tuple(cls.__str__() for cls in expected_classes)
        with self.subTest(msg=f'Testing that the classes of the individuals '
                              f'({", ".join(expected_names)}) '
                              f'coincide with the expectation (by hash).'):
            for loaded_classes in loaded_classes_for_object:
                self.assertItemsEqual(expected_classes, loaded_classes)

    def test_relationships(self):
        """Checks the loaded relationships between CUDS objects."""
        for i in range(1, 4):
            cuds = self.object[i]
            neighbor = cuds.get(rel=test_general_rdf_import.isLeftOf)
            self.assertIs(neighbor, self.object[i + 1])
            neighbor = cuds.get(rel=test_general_rdf_import.isNextTo)
            self.assertIs(neighbor, self.object[i + 1])
