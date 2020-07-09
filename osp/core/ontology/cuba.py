from rdflib.namespace import ClosedNamespace
from rdflib import URIRef

ENTITIES = [
    "activeRelationship", "Entity", "File", "Nothing",
    "passiveRelationship", "path", "Wrapper", "attribute",
    "relationship", "Class"
]

HIDDEN = [
    "_default", "_default_attribute", "_default_value",
    "_default_rel", "_length", "_shape", "_dtype",
]

DTYPE_PREFIXES = [
    "datatypes/STRING-",
    "datatypes/VECTOR-"
]


class _CubaNamespace(ClosedNamespace):
    """
    Closed namespace for RDF terms
    """

    def __init__(self):
        super(_CubaNamespace, self).__init__(
            URIRef("http://www.osp-core.com/cuba#"),
            terms=ENTITIES + HIDDEN + DTYPE_PREFIXES
        )

    def term(self, name):
        if name.startswith("datatypes/"):
            return URIRef("%s_%s" % (self.uri, name))
        return super(_CubaNamespace, self).term(name)

    def __contains__(self, name):
        return name in ENTITIES or name in HIDDEN \
            or any(name.startswith(x) for x in DTYPE_PREFIXES)


rdflib_cuba = _CubaNamespace()
