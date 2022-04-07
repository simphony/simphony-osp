"""This method contains an rdflib namespace for the CUBA namespace."""

from rdflib import URIRef
from rdflib import __version__ as rdflib_version
from rdflib.namespace import ClosedNamespace

NAMESPACE_IRI = "http://www.osp-core.com/cuba#"

ENTITIES = [
    "activeRelationship",
    "Entity",
    "File",
    "Nothing",
    "passiveRelationship",
    "path",
    "Wrapper",
    "attribute",
    "relationship",
    "Class",
]

HIDDEN = [
    "_default",
    "_default_attribute",
    "_default_value",
    "_default_rel",
    "_length",
    "_shape",
    "_dtype",
    "_reference_by_label",
    "_serialization",
]

DTYPE_PREFIXES = ["_datatypes/STRING-", "_datatypes/VECTOR-"]


class _CubaNamespace(ClosedNamespace):
    """Closed namespace for RDF terms."""

    if rdflib_version >= "6":

        def __new__(cls, *args, **kwargs):
            kwargs.setdefault("uri", URIRef(NAMESPACE_IRI))
            kwargs.setdefault("terms", ENTITIES + HIDDEN + DTYPE_PREFIXES)
            return super().__new__(cls, *args, **kwargs)

    else:

        def __init__(self):
            super(_CubaNamespace, self).__init__(
                URIRef(NAMESPACE_IRI), terms=ENTITIES + HIDDEN + DTYPE_PREFIXES
            )

    def term(self, name):
        if name.startswith("_datatypes/"):
            return URIRef("%s%s" % (self.uri, name))
        return super(_CubaNamespace, self).term(name)

    def __contains__(self, name):
        if isinstance(name, URIRef):
            if not name.startswith(NAMESPACE_IRI):
                return False
            name = name[len(NAMESPACE_IRI) :]
        return (
            name in ENTITIES
            or name in HIDDEN
            or any(name.startswith(x) for x in DTYPE_PREFIXES)
        )


rdflib_cuba = _CubaNamespace()
