from osp.core.namespaces import math
from osp.core.ontology.restriction import TYPE


for r in math.Integer.restrictions:
    print(r.rtype)
    if r.rtype == TYPE.RELATIONSHIP_RESTRICTION:
        print(r.relationship)
    else:
        print(r.attribute)
    print(r.quantifier)
    print(r.target)
    print()
