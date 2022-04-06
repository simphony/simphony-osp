"""Abstract superclass of any entity in the ontology."""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache

import rdflib

logger = logging.getLogger(__name__)

# The properties of the instances of the class OntologyEntity defined below
# may be cached by applying the decorator @lru_cache after the @property
# decorator. The following parameter fixes the maximum number of different
# instances of OntologyEntity for which a property may be cached.
entity_cache_size = 1024


class OntologyEntity(ABC):
    """Abstract superclass of any entity in the ontology."""

    @abstractmethod
    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        """Initialise the ontology entity.

        Args:
            namespace_registry (OntologyNamespaceRegistry): The namespace
                registry.
            namespace_iri (rdflib.URIRef): The namespace of the entity
            name (str): The name of the entity
            iri_suffix (str): namespace_iri + iri_suffix is namespace of the
                entity.
        """
        self._name = name
        self._iri_suffix = iri_suffix
        self._namespace_iri = namespace_iri
        self._namespace_registry = namespace_registry

    @property
    def _namespace_name(self):
        return self._namespace_registry._get_namespace_name_and_iri(self.iri)[
            0
        ]

    def __str__(self):
        """Transform the entity into a human readable string."""
        return "%s.%s" % (self._namespace_name, self._name)

    def __repr__(self):
        """Transform the entity into a string."""
        return "<%s %s.%s>" % (
            self.__class__.__name__,
            self._namespace_name,
            self._name,
        )

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
        """Get the name used in storage backends to store instances."""
        return "%s___%s" % (self._namespace_name, self._iri_suffix)

    @property
    def namespace(self):
        """Get the namespace object of the entity."""
        return self._namespace_registry.namespace_from_iri(self._namespace_iri)

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity.

        Returns:
            List[OntologyEntity]: The direct superclasses of the entity

        """
        return set(self._direct_superclasses())

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity.

        Returns:
            Set[OntologyEntity]: The direct subclasses of the entity

        """
        return set(self._direct_subclasses())

    @property
    @lru_cache(maxsize=entity_cache_size)
    def subclasses(self):
        """Get the subclasses of the entity.

        Returns:
            Set[OntologyEntity]: The direct subclasses of the entity

        """
        return set(self._subclasses())

    @property
    @lru_cache(maxsize=entity_cache_size)
    def superclasses(self):
        """Get the superclass of the entity.

        Returns:
            Set[OntologyEntity]: The direct superclasses of the entity

        """
        return set(self._superclasses())

    @property
    def description(self):
        """Get the description of the entity.

        Returns:
            str: The description of the entity

        """
        desc = self.namespace._graph.value(
            self.iri, rdflib.RDFS.isDefinedBy, None
        )
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
            bool: Whether self is a superclass of other.
        """
        return self in other.superclasses

    def is_subclass_of(self, other):
        """Perform a subclass check.

        Args:
            other (Entity): The other entity.

        Returns:
            bool: Whether self is a subclass of other.

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

    def _transitive_hull(self, predicate_iri, inverse=False, blacklist=()):
        """Get all the entities connected with the given predicate.

        Args:
            predicate_iri (URIRef): The IRI of the predicate
            inverse (bool, optional): Use the inverse instead.
                Defaults to False.
            blacklist (collection): A collection of IRIs not to return.

        Yields:
            OntologyEntity: The connected entities
        """
        visited = {self.iri}
        frontier = {self.iri}
        while frontier:
            current = frontier.pop()
            yield from self._directly_connected(
                predicate_iri=predicate_iri,
                inverse=inverse,
                blacklist=blacklist,
                _frontier=frontier,
                _visited=visited,
                _iri=current,
            )

    def _special_cases(self, triple):
        """Some supclass statements are often omitted in the ontology.

        Replace these with safer triple patterns.

        Args:
            triple (Tuple[rdflib.term]): A triple pattern to possibly replace.

        Returns:
            triple (Tuple[rdflib.term]): Possibly replaced triple.
        """
        if triple == (None, rdflib.RDFS.subClassOf, rdflib.OWL.Thing):
            return (None, rdflib.RDF.type, rdflib.OWL.Class)
        if triple == (rdflib.OWL.Nothing, rdflib.RDFS.subClassOf, None):
            return (None, rdflib.RDF.type, rdflib.OWL.Class)

        if triple == (
            None,
            rdflib.RDFS.subPropertyOf,
            rdflib.OWL.topObjectProperty,
        ):
            return (None, rdflib.RDF.type, rdflib.OWL.ObjectProperty)
        if triple == (
            rdflib.OWL.bottomObjectProperty,
            rdflib.RDFS.subPropertyOf,
            None,
        ):
            return (None, rdflib.RDF.type, rdflib.OWL.ObjectProperty)

        if triple == (
            None,
            rdflib.RDFS.subPropertyOf,
            rdflib.OWL.topDataProperty,
        ):
            return (None, rdflib.RDF.type, rdflib.OWL.DataProperty)
        if triple == (
            rdflib.OWL.bottomDataProperty,
            rdflib.RDFS.subPropertyOf,
            None,
        ):
            return (None, rdflib.RDF.type, rdflib.OWL.DataProperty)
        return triple

    def _directly_connected(
        self,
        predicate_iri,
        inverse=False,
        blacklist=(),
        _frontier=None,
        _visited=None,
        _iri=None,
    ):
        """Get all the entities directly connected with the given predicate.

        Args:
            predicate_iri (URIRef): The IRI of the predicate
            inverse (bool, optional): Use the inverse instead.
                Defaults to False.
            blacklist (collection): A collection of IRIs not to return.
            Others: Helper for _transitive_hull method.

        Yields:
            OntologyEntity: The connected entities
        """
        triple = (_iri or self.iri, predicate_iri, None)
        if inverse:
            triple = (None, predicate_iri, _iri or self.iri)

        if predicate_iri in [
            rdflib.RDFS.subClassOf,
            rdflib.RDFS.subPropertyOf,
        ]:
            triple = self._special_cases(triple)
        for x in self.namespace._graph.triples(triple):
            o = x[0 if triple[0] is None else 2]
            if _visited and o in _visited:
                continue
            if not isinstance(o, rdflib.BNode):
                if _visited is not None:
                    _visited.add(o)
                if _frontier is not None:
                    _frontier.add(o)
                if o not in blacklist:
                    x = self.namespace._namespace_registry.from_iri(
                        o, raise_error=False
                    )
                    if x:
                        yield x

    def __hash__(self):
        """Make the entity hashable."""
        return hash(self.iri)
