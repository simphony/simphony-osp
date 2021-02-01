"""Small test for restrictions."""

from osp.core.ontology.restriction import TYPE

try:
    from osp.core.namespaces import math
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("emmo")
    _namespace_registry.update_namespaces()
    math = _namespace_registry.math


for r in math.Integer.restrictions:
    print(r.rtype)
    if r.rtype == TYPE.RELATIONSHIP_RESTRICTION:
        print(r.relationship)
    else:
        print(r.attribute)
    print(r.quantifier)
    print(r.target)
    print()
