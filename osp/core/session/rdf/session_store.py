# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import rdflib
import uuid
from osp.core import ONTOLOGY_NAMESPACE_REGISTRY, get_entity
from osp.core.ontology import OntologyRelationship

UID_NAMESPACE_PREFIX = "uid"
UID_NAMESPACE = "uid#"  # "http://osp-core.com/cuds/uid#"
_IRI_PREFIX = ""  # "http://"
_ENTITY_IRI_SEPARATOR = "#"  # ".osp-core.com/entity#"
ENTITY_NAMESPACE = _IRI_PREFIX + "%s" + _ENTITY_IRI_SEPARATOR


def get_entity_from_iri(iri):
    iri = str(iri)[len(_IRI_PREFIX):]
    return get_entity(iri.replace(_ENTITY_IRI_SEPARATOR, "."))

class SessionRDFLibStore(rdflib.store.Store):
    """RDFLib store for sessions."""

    context_aware = True
    formula_aware = True
    graph_aware = True

    def __init__(self, session):
        self.session = session

    def triples(self, triple_pattern, context=None):
        s, p, o = triple_pattern
        if not isinstance(s, rdflib.term.URIRef) or not str(s).startswith(UID_NAMESPACE):
            raise NotImplementedError
        s_cuds = self.session.load(uuid.UUID(s[len(UID_NAMESPACE):])).one()

        if p is None:
            for o_cuds, rel in s_cuds.get(return_rel=True):
                if o is None or o == o_cuds.get_iri():
                    yield (s_cuds.get_iri(), rel.get_iri(), o_cuds.get_iri()), self.context
            for attribute, value in s_cuds.get_attributes().items():
                if o is None or o.eq(value):
                    yield (s_cuds.get_iri(), attribute.get_iri(), rdflib.term.Literal(value)), self.context
        else:
            rel = get_entity_from_iri(p)
            if isinstance(rel, OntologyRelationship):
                for o_cuds in s_cuds.get(rel=rel):
                    if o is None or o == o_cuds.get_iri():
                        yield (s_cuds.get_iri(), rel.get_iri(), o_cuds.get_iri()), self.context
            else:
                if o is None or o.eq(s_cuds.get_attributes()[rel]):
                    yield (s_cuds.get_iri(), rel.get_iri(), rdflib.term.Literal(s_cuds.get_attributes()[rel])), self.context

    def namespaces(self):
        result = [(UID_NAMESPACE_PREFIX, rdflib.term.URIRef(UID_NAMESPACE))]
        for namespace in ONTOLOGY_NAMESPACE_REGISTRY:
            result.append((namespace.name.lower(),
                           rdflib.term.URIRef(ENTITY_NAMESPACE % namespace.name.lower())))
        return result
    
    def context(self):
        yield from []
