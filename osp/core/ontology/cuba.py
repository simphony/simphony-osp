from rdflib.namespace import ClosedNamespace
from rdflib import URIRef


class _CubaNamespace(ClosedNamespace):
    """
    Closed namespace for RDF terms
    """

    def __init__(self):
        super(_CubaNamespace, self).__init__(
            URIRef("http://www.osp-core.com/CUBA#"),
            terms=[
                "_default", "_default_attribute", "_default_value",
                "_default_rel", "_length", "_shape", "_dtype",
                "ACTIVE_RELATIONSHIP", "ENTITY", "FILE", "NOTHING",
                "PASSIVE_RELATIONSHIP", "PATH", "WRAPPER", "ATTRIBUTE",
                "RELATIONSHIP", "CLASS", "datatypes/STRING-",
                "datatypes/VECTOR-"
            ]
        )

    def term(self, name):
        if name.startswith("datatypes/"):
            return URIRef("%s_%s" % (self.uri, name))
        return super(_CubaNamespace, self).term(name)


rdflib_cuba = _CubaNamespace()
