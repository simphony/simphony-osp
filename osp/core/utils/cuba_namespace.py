"""This method contains an rdflib namespace for the CUBA namespace."""

from rdflib import URIRef
from rdflib.namespace import ClosedNamespace

NAMESPACE_IRI = "http://www.osp-core.com/cuba#"

ENTITIES = [
    "activeRelationship", "Entity", "File", "Nothing",
    "passiveRelationship", "path", "Wrapper", "attribute",
    "relationship", "Class", "Container", "contains",
]

HIDDEN = [
    "_default", "_default_attribute", "_default_value",
    "_default_rel", "_length", "_shape", "_dtype", "_reference_by_label",
    "_serialization"
]


class _CubaNamespace(ClosedNamespace):
    """Closed namespace for RDF terms."""

    def __new__(cls, *args, **kwargs):
        kwargs.setdefault('uri', URIRef(NAMESPACE_IRI))
        kwargs.setdefault('terms', ENTITIES + HIDDEN)
        return super().__new__(cls, *args, **kwargs)

    def __contains__(self, name):
        if isinstance(name, URIRef):
            if not name.startswith(NAMESPACE_IRI):
                return False
            name = name[len(NAMESPACE_IRI):]
        return name in ENTITIES or name in HIDDEN


cuba_namespace = _CubaNamespace()
