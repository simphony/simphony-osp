"""Test the API with the EMMO ontology."""

import unittest2 as unittest
from osp.core.ontology.oclass_restriction import RTYPE

try:
    from osp.core.namespaces import math
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("emmo")
    _namespace_registry.update_namespaces()
    math = _namespace_registry.math


class TestRestrictionsEmmo(unittest.TestCase):

    def test_emmo_datatypes(self):
        for r in math.Integer.restrictions:
            print(r.rtype)
            print(r)
            print()


if __name__ == "__main__":
    unittest.main()
