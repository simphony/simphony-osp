# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.ontology.entity import OntologyEntity
import logging
import rdflib

logger = logging.getLogger(__name__)

# TODO characteristics


class OntologyRelationship(OntologyEntity):
    def __init__(self, namespace, name):
        super().__init__(namespace, name)
        logger.debug("Create ontology object property %s" % self)

    @property
    def inverse(self):
        triple1 = (self.iri, rdflib.OWL.inverseOf, None)
        triple2 = (None, rdflib.OWL.inverseOf, self.iri)
        for _, _, o in self.namespace._graph.triples(triple1):
            return self.namespace._namespace_registry.from_iri(o)
        for s, _, _ in self.namespace._graph.triples(triple2):
            return self.namespace._namespace_registry.from_iri(s)
        return self._add_inverse()

    def _direct_superclasses(self):
        return self._directly_connected(rdflib.RDFS.subPropertyOf)

    def _direct_subclasses(self):
        return self._directly_connected(rdflib.RDFS.subPropertyOf,
                                        inverse=True)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(rdflib.RDFS.subPropertyOf)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(rdflib.RDFS.subPropertyOf,
                                         inverse=True)
