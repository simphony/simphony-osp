"""Abstract superclass of any entity in the ontology."""

from abc import ABC, abstractmethod
import rdflib
import logging

logger = logging.getLogger(__name__)


class OntologyEntity(ABC):
    """Abstract superclass of any entity in the ontology."""

    @abstractmethod
    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        """Initialise the ontology entity.

        :param namespace_iri: The namespace of the entity
        :type namespace_iri: URIRef
        :param name: The name of the entity
        :type name: str
        """
        self._name = name
        self._iri_suffix = iri_suffix
        self._namespace_iri = namespace_iri
        self._namespace_registry = namespace_registry

    @property
    def _namespace_name(self):
        return self._namespace_registry._get_namespace_name_and_iri(
            self.iri
        )[0]

    def __str__(self):
        """Transform the entity into a human readable string."""
        return "%s.%s" % (self._namespace_name, self._name)

    def __repr__(self):
        """Transform the entity into a string."""
        return "<%s %s.%s>" % (self.__class__.__name__,
                               self._namespace_name, self._name)

    def __eq__(self, other):
        """Check whether two entities are the same.

        Args:
            other (OntologyEntity): The other entity.

        Returns:
            bool: Whether the two entities are the same.
        """
        return isinstance(other, OntologyEntity) and self.iri == other.iri

    @property
    def name(self):
        """Get the name of the entity."""
        return self._name

    @property
    def iri(self):
        """Get the IRI of the Entity."""
        return rdflib.URIRef(self._namespace_iri + self._iri_suffix)

    @property
    def tblname(self):
        """The name used in storage backends to store instances."""
        return "%s___%s" % (self._namespace_name, self._iri_suffix)

    @property
    def namespace(self):
        """Get the namespace object of the entity."""
        return self._namespace_registry.namespace_from_iri(self._namespace_iri)

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity.

        :return: The direct superclasses of the entity
        :rtype: List[OntologyEntity]
        """
        return set(self._direct_superclasses())

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity.

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._direct_subclasses())

    @property
    def subclasses(self):
        """Get the subclasses of the entity.

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._subclasses())

    @property
    def superclasses(self):
        """Get the superclass of the entity.

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return set(self._superclasses())

    @property
    def description(self):
        """Get the description of the entity.

        :return: The description of the entity
        :rtype: str
        """
        desc = self.namespace._graph.value(
            self.iri, rdflib.RDFS.isDefinedBy, None)
        if desc is None:
            return "To Be Determined"
        return str(desc)

    def get_triples(self):
        """Get the triples of the entity."""
        return self.namespace._graph.triples((self.iri, None, None))

    def is_superclass_of(self, other):
        """Perform a superclass check.

        Args:
            other (Entity): The other entity.

        Returns:
            True: Whether self is a superclass of other.
        """
        return self in other.superclasses

    def is_subclass_of(self, other):
        """Perform a subclass check.

        Args:
            other (Entity): The other entity.

        Returns:
            True: Whether self is a subclass of other.
        """
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
        """Get all the entities connected with the given predicate.

        Args:
            predicate_iri (URIRef): The IRI of the predicate
            inverse (bool, optional): Use the inverse instead.
                Defaults to False.

        Yields:
            OntologyEntity: The connected entities
        """
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
        """Get all the entities directly connected with the given predicate.

        Args:
            predicate_iri (URIRef): The IRI of the predicate
            inverse (bool, optional): Use the inverse instead.
                Defaults to False.

        Yields:
            OntologyEntity: The connected entities
        """
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
        """Make the entity hashable."""
        return hash(self.iri)
