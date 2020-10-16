"""Test the API of CUDS objects using the foaf ontology."""

import unittest2 as unittest
import uuid

from osp.core.namespaces import cuba

try:
    from osp.core.namespaces import foaf
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("foaf")
    _namespace_registry.update_namespaces()
    foaf = _namespace_registry.foaf


class TestAPIfoaf(unittest.TestCase):
    """Test the API of CUDS objects using the foaf ontology."""

    def test_creation(self):
        """Test creation of objectes are possible."""
        c = foaf.Person()
        self.assertTrue(c.is_a(foaf.Person))
        self.assertTrue(c.is_a(cuba.Class))

    def test_uid(self):
        """Test that the uid variable contains a UUID object."""
        c = foaf.Person()
        self.assertIsInstance(c.uid, uuid.UUID)

    def test_relations(self):
        """Test some relationships."""
        a = foaf.Person()
        b = foaf.Person()
        b.add(a, rel=foaf.knows)
        self.assertEqual(b.get(rel=foaf.knows), [a])

    def test_throw_exception(self):
        """Test some exceptions.""" 
        c = foaf.Person()
        c.age = 20
        # self.assertRaises(AttributeError, c.__setattr__, "age", "2.2")


if __name__ == '__main__':
    unittest.main()
