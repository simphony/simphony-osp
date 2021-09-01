"""Abstract Base Class for all Sessions."""

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Iterator, List, Optional, Tuple, Set, TYPE_CHECKING, Union

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef
from rdflib.term import Identifier

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.datatypes import UID
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.session.result import returns_query_result
# from osp.core.utils.general import uid_from_general_iri

if TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity

entity_cache_size: int = 1024


class Session(ABC):
    """Abstract Base Class for all Sessions.

    Defines the common standard API and sets the registry.
    """
    label_properties: Tuple[URIRef] = (SKOS.prefLabel, RDFS.label)

    @property
    def graph(self) -> Graph:
        return self._graph

    # Initialize or close session
    # ↓-------------------------↓

    def __init__(self):
        """Initialize the session."""
        self._graph = rdflib.Graph()
        self._storing = list()

    def close(self):
        """Close the connection to the backend."""
        pass

    def __enter__(self):
        """Establish the connection to the backend."""
        pass

    def __exit__(self, *args):
        """Close the connection to the backend."""
        pass

    # ↑-------------------------↑
    # Initialize or close session

    # Access content stored in the session (session's bag)
    # ↓--------------------------------------------------↓

    def __iter__(self) -> Iterator['OntologyEntity']:
        # Warning: entities can be repeated.
        return (self.from_identifier(identifier)
                for identifier in self.iter_identifiers())

    def iter_identifiers(self) -> Iterator[Identifier]:
        # Warning: identifiers can be repeated.
        supported_types = frozenset({OWL.DatatypeProperty,
                                     OWL.ObjectProperty,
                                     OWL.Class,
                                     OWL.Restriction})
        return (s for t in supported_types
                for s in self._graph.subjects(RDF.type, t))

    def iter_labels(self,
                    entity: Optional[Union[
                        Identifier,
                        'OntologyEntity']] = None,
                    lang: Optional[str] = None,
                    return_prop: bool = False,
                    return_literal: bool = True
                    ) -> Iterator[Union[Literal,
                                        str,
                                        Tuple[Literal, URIRef],
                                        Tuple[str, URIRef]]]:
        from osp.core.ontology.entity import OntologyEntity
        if isinstance(entity, OntologyEntity):
            entity = entity.identifier

        def filter_language(literal):
            if lang is None:
                return True
            elif lang == "":
                return literal.language is None
            else:
                return literal.language == lang

        labels = filter(lambda label_tuple: filter_language(label_tuple[1]),
                        ((prop, literal) for prop in self.label_properties
                         for literal in self._graph.objects(entity, prop))
                        )
        if not return_prop and not return_literal:
            return (str(x[1]) for x in labels)
        elif return_prop and not return_literal:
            return ((str(x[1]), x[0]) for x in labels)
        elif not return_prop and return_literal:
            return (x[1] for x in labels)
        else:
            return ((x[1], x[0]) for x in labels)

    def get_identifiers(self) -> Set[Identifier]:
        return set(self.iter_identifiers())

    def get_entities(self) -> Set['OntologyEntity']:
        return set(x for x in self)

    def store(self, entity: 'OntologyEntity') -> None:
        """Store a copy of given ontology entity in the session.

        Args:
            entity: The ontology entity to store.
        """
        for t in entity.triples:
            self._graph.add(t)

    def remove(self, entity: 'OntologyEntity'):
        """Remove the triples describing the ontology entity."""
        self._graph.remove((entity.identifier, None, None))

    @lru_cache(maxsize=entity_cache_size)
    def from_identifier(self, identifier: Identifier) -> 'OntologyEntity':
        """Get an entity from its identifier.

        Args:
            identifier: The identifier of the entity.

        Raises:
            KeyError: The ontology entity is not stored in this session.

        Returns:
            The OntologyEntity.
        """
        from osp.core.ontology.oclass_composition import \
            get_composition
        from osp.core.ontology.oclass_restriction import \
            get_restriction
        # TODO: make return type hint more specific.
        supported_types = frozenset({OWL.DatatypeProperty,
                                     OWL.ObjectProperty,
                                     OWL.Class,
                                     OWL.Restriction})
        # TODO: Use transitive closure just in case a subclass is identified.
        for o in self.graph.objects(identifier, RDF.type):
            if o not in supported_types:
                continue
            if o == OWL.DatatypeProperty:
                return OntologyAttribute(UID(identifier), session=self)
            elif o == OWL.ObjectProperty:
                return OntologyRelationship(UID(identifier), session=self)
            elif o == OWL.Class:
                x = get_composition(o, self)
                return x or OntologyClass(UID(identifier), session=self)
            elif o == OWL.Restriction:
                x = get_restriction(o, self)
                if x:
                    return x
        else:
            raise KeyError(f"Identifier {identifier} not found in graph or "
                           f"not of any type in the set {supported_types}.")

    # Access content stored in the session (session's bag)
    # ↑--------------------------------------------------↑

    #@returns_query_result
    #def load_from_iri(self, *iris):
    #    """Load the cuds_objects with the given iris.

    #    Args:
    #        *iri (URIRef): The IRIs of the cuds_objects to load.

    #    Yields:
    #        Cuds: The fetched Cuds objects.
    #    """
    #    pass
    #    # return self.load(*[uid_from_general_iri(iri, self.graph)[0]
    #    #                    for iri in iris])

    def delete_cuds_object(self, cuds_object):
        """Remove a CUDS object.

        Will not delete the cuds objects contained.

        Args:
            cuds_object (Cuds): The CUDS object to be deleted
        """
        pass

    @abstractmethod
    def _notify_delete(self, cuds_object):
        """Notify the session that some object has been deleted.

        Args:
            cuds_object (Cuds): The cuds_object that has been deleted
        """

    @abstractmethod
    def _notify_update(self, cuds_object):
        """Notify the session that some object has been updated.

        Args:
            cuds_object (Cuds): The cuds_object that has been updated.
        """

    @abstractmethod
    def _notify_read(self, cuds_object):
        """Notify the session that given cuds object has been read.

        This method is called when the user accesses the attributes or the
        relationships of the cuds_object cuds_object.

        Args:
            cuds_object (Cuds): The cuds_object that has been accessed.
        """

    @abstractmethod
    def _get_full_graph(self):
        """Get the RDF Graph including objects only present in the backend."""

    @abstractmethod
    def __str__(self):
        """Convert the session to string."""
