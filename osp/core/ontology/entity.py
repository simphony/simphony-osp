"""Abstract superclass of any entity in the ontology."""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Iterable, Iterator, Optional, Set, Tuple, TYPE_CHECKING,\
    Union

from rdflib import Graph, Literal, URIRef
from rdflib.term import Identifier

from osp.core.ontology.datatypes import Triple, UID

if TYPE_CHECKING:
    from osp.core.session.session import Session


logger = logging.getLogger(__name__)

# The properties of the instances of the class OntologyEntity defined below
# may be cached by applying the decorator @lru_cache after the @property
# decorator. The following parameter fixes the maximum number of different
# instances of OntologyEntity for which a property may be cached.
entity_cache_size = 1024


class OntologyEntity(ABC):
    """Abstract superclass of any entity in the ontology."""

    # Public API
    # ↓ ------ ↓

    @property
    def iri(self) -> URIRef:
        """Get the IRI of the Entity.

        Raises:
            TypeError: When the identifier of the ontology entity is a blank
                node.
        """
        return self.uid.to_iri()

    @property
    def identifier(self) -> Identifier:
        """Get the Identifier (URIRef or BNode) representing the entity."""
        return self.uid.to_identifier()

    @property
    def label(self) -> Optional[str]:
        """Get the preferred label of this entity, if it exists.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        return str(self.label_literal) \
            if self.label_literal is not None else None

    @property
    def session(self) -> 'Session':
        """The session where the entity is stored."""
        return self._session

    @session.setter
    def session(self, value: 'Session') -> None:
        """Change the session where the entity is stored.

        Equivalent to removing the item from the previous session and adding it
        to the new session.
        """
        # THIS SETTER IS ONLY FOR THE USER. DO NOT USE IT AS DEVELOPER,
        # USE `Session.store` instead, the responsibility of storing should
        # be on the session not on the entity.
        value.store(self)
        if self._session is not value:
            self._session.delete(self)
        self._session = value

    @property
    @lru_cache(maxsize=entity_cache_size)
    def direct_superclasses(self) -> Set['OntologyEntity']:
        """Get the direct superclasses of the entity.

        Returns:
            The direct superclasses of the entity.
        """
        return set(self._get_direct_superclasses())

    @property
    @lru_cache(maxsize=entity_cache_size)
    def direct_subclasses(self) -> Set['OntologyEntity']:
        """Get the direct subclasses of the entity.

        Returns:
            The direct subclasses of the entity.
        """
        return set(self._get_direct_subclasses())

    @property
    @lru_cache(maxsize=entity_cache_size)
    def superclasses(self) -> Set[Union['OntologyEntity']]:
        """Get the superclass of the entity.

        Returns:
            The direct superclasses of the entity.

        """
        return set(self._get_superclasses())

    @property
    @lru_cache(maxsize=entity_cache_size)
    def subclasses(self) -> Set['OntologyEntity']:
        """Get the subclasses of the entity.

        Returns:
            The direct subclasses of the entity

        """
        return set(self._get_subclasses())

    def is_superclass_of(self, other: 'OntologyEntity') -> bool:
        """Perform a superclass check.

        Args:
            other: The other ontology entity.

        Returns:
            Whether self is a superclass of other.
        """
        return self in other.superclasses

    def is_subclass_of(self, other: 'OntologyEntity') -> bool:
        """Perform a subclass check.

        Args:
            other: The other entity.

        Returns:
            bool: Whether self is a subclass of other.

        """
        return self in other.subclasses

    # ↑ ------ ↑
    # Public API

    @property
    def uid(self) -> UID:
        """Get the unique identifier that OSP-core uses for this entity."""
        return self._uid

    @uid.setter
    def uid(self, value: UID) -> None:
        """Set the unique identifier that OSP-core uses for this entity."""
        self._uid = value

    @property
    def label_lang(self) -> Optional[str]:
        """Get the language of the preferred label of this entity.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        return self.label_literal.language \
            if self.label_literal is not None else None

    @property
    def label_literal(self) -> Optional[Literal]:
        """Get the preferred label for this entity.

        The labels are first sorted by the property defining them (which is
        an attribute of the session that this entity is stored on), and then by
        their length.

        Returns:
            The first label in the resulting ordering is returned. If the
            entity has no label, then None is returned.
        """
        labels = self.iter_labels(return_literal=True,
                                  return_prop=True)
        # Sort by label property preference, and length.
        labels = sorted(labels,
                        key=lambda x:
                        (self.session.label_properties.index(x[1]),
                         len(x[0])))
        # Return the first label
        return labels[0][0] if len(labels) > 0 else None

    def iter_labels(self,
                    lang: Optional[str] = None,
                    return_prop: bool = False,
                    return_literal: bool = True) -> \
            Iterator[Union[Literal,
                           str,
                           Tuple[str, URIRef],
                           Tuple[Literal, URIRef]]]:
        """Returns all the available labels for this ontology entity.

        Args:
            lang: retrieve labels only in a specific language.
            return_prop: Whether to return the property that designates the
                label. When active, it is the second argument.
            return_literal: Whether to return a literal or a string with the
                label (the former contains the language, the latter not).

        Returns:
            An iterator yielding strings or literals; or tuples whose first
            element is a string or literal, and second element the property
            defining this label.
        """
        return self.session.iter_labels(entity=self, lang=lang,
                                        return_literal=return_literal,
                                        return_prop=return_prop)

    @property
    def triples(self) -> Set[Triple]:
        """Get the triples defining the entity."""
        if self.__graph is not None:
            return set(self.__graph.triples((None, None, None)))
        else:
            return set(self.session.graph.triples((self.identifier, None,
                                                   None)))

    @abstractmethod
    def _get_direct_superclasses(self) -> Iterable['OntologyEntity']:
        """Direct superclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def _get_direct_subclasses(self) -> Iterable['OntologyEntity']:
        """Direct subclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def _get_superclasses(self) -> Iterable['OntologyEntity']:
        """Superclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def _get_subclasses(self) -> Iterable['OntologyEntity']:
        """Subclass getter specific to the type of ontology entity."""
        pass

    __graph: Optional[Graph] = None  # Only exists during initialization.

    @abstractmethod
    def __init__(self,
                 uid: UID,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None) -> None:
        """Initialize the ontology entity.

        Args:
            uid: UID identifying the entity.
            session: Session where the entity is stored.
            triples: Construct the entity with the provided triples.
        """
        if uid is None:
            uid = UID()
        elif not isinstance(uid, UID):
            raise Exception(f"Tried to initialize an ontology entity with "
                            f"uid {uid}, which is not a UID object.")
        self._uid = uid

        # While the entity is being initialized, it belongs to no session.
        # The extra triples are added to the `__graph` attribute. While such
        # attribute exists, it is the preferred way to access the entity's
        # triples using the `triples` property.
        self._session = None
        if triples is not None:
            self.__graph = Graph()
            for s, p, o in triples:
                if s != self.identifier:
                    raise ValueError("Trying to add extra triples to an "
                                     "ontology entity with a subject that "
                                     "does not match the individual's "
                                     "identifier.")
                self.__graph.add((s, p, o))
        if session is None:
            from osp.core.session.session import Session
            session = Session.default_session
        if self.__graph is not None:
            # Only change what is stored in the session if custom triples were
            # provided.
            session.store(self)
        self._session = session
        self.__graph = None

    def __str__(self) -> str:
        """Transform the entity into a human readable string."""
        return f"{self.uid}"

    def __repr__(self) -> str:
        """Transform the entity into a string."""
        return f"<{self.__class__.__name__}: {self.uid}>"

    def __eq__(self, other: 'OntologyEntity') -> bool:
        """Check whether two entities are the same.

        Args:
            other: The other entity.

        Returns:
            bool: Whether the two entities are the same.
        """
        # TODO: Blank nodes with different IDs.
        return isinstance(other, OntologyEntity) \
            and self.session == other.session \
            and self.uid == other.uid

    def __hash__(self) -> int:
        """Make the entity hashable."""
        return hash((self.uid, self.session))
