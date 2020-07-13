# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod
import rdflib
import logging

logger = logging.getLogger(__name__)


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, namespace, name, iri_suffix):
        """Initialise the ontology entity

        :param namespace: The namespace of the entity
        :type namespace: OntologyNamespace
        :param name: The name of the entity
        :type name: str
        """
        self._name = name
        self._iri_suffix = iri_suffix
        self._namespace = namespace

    def __str__(self):
        return "%s.%s" % (self.namespace._name, self._name)

    def __repr__(self):
        return "<%s %s.%s>" % (
            self.__class__.__name__,
            self._namespace._name,
            self._name
        )

    def __eq__(self, other):
        return isinstance(other, OntologyEntity) and self.iri == other.iri

    @property
    def name(self):
        """Get the name of the entity"""
        return self._name

    @property
    def iri(self):
        """Get the IRI of the Entity"""
        return rdflib.URIRef(self._namespace.get_iri() + self._iri_suffix)

    @property
    def tblname(self):
        return "%s___%s" % (self.namespace._name, self._iri_suffix)

    @property
    def namespace(self):
        """Get the name of the entity"""
        return self._namespace

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: List[OntologyEntity]
        """
        return set(self._direct_superclasses())

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._direct_subclasses())

    @property
    def subclasses(self):
        """Get the subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._subclasses())

    @property
    def superclasses(self):
        """Get the superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._superclasses())

    @property
    def description(self):
        """Get the description of the entity

        :return: The description of the entity
        :rtype: str
        """
        desc = self.namespace._graph.value(
            self.iri, rdflib.RDFS.isDefinedBy, None)
        if desc is None:
            return "To Be Determined"
        return str(desc)

    def get_triples(self):
        """ Get the triples of the entity """
        return self.namespace._graph.triples((self.iri, None, None))

    def is_superclass_of(self, other):
        return self in other.superclasses

    def is_subclass_of(self, other):
        return self in other.subclasses

    @abstractmethod
    def _direct_superclasses(self):
        pass

    @abstractmethod
    def _direct_subclasses(self):
        pass

    @abstractmethod
    def _superclasses(self):
        pass

    @abstractmethod
    def _subclasses(self):
        pass

    def _transitive_hull(self, predicate_iri, inverse=False):
        result = {self.iri}
        frontier = {self.iri}
        while frontier:
            current = frontier.pop()
            triple = (current, predicate_iri, None)
            if inverse:
                triple = (None, predicate_iri, current)
            for x in self.namespace._graph.triples(triple):
                o = x[0 if inverse else 2]
                if o not in result and not isinstance(o, rdflib.BNode) \
                    and not str(o).startswith((str(rdflib.RDF),
                                               str(rdflib.RDFS),
                                               str(rdflib.OWL))):
                    frontier.add(o)
                    result.add(o)
                    yield self.namespace._namespace_registry.from_iri(o)

    def _directly_connected(self, predicate_iri, inverse=False):
        triple = (self.iri, predicate_iri, None)
        if inverse:
            triple = (None, predicate_iri, self.iri)
        for x in self.namespace._graph.triples(triple):
            o = x[0 if inverse else 2]
            if not isinstance(o, rdflib.BNode) \
                and not str(o).startswith((str(rdflib.RDF),
                                           str(rdflib.RDFS),
                                           str(rdflib.OWL))):
                yield self.namespace._namespace_registry.from_iri(o)

    def __hash__(self):
        return hash(self.iri)
