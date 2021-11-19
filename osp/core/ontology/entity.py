"""Abstract superclass of any entity in the ontology."""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import (Iterable, Iterator, List, Optional, Set, Tuple,
                    TYPE_CHECKING, Union)

from rdflib import Graph, Literal, URIRef
from rdflib.term import Identifier

from osp.core.ontology.datatypes import Triple, UID

if TYPE_CHECKING:
    from osp.core.ontology.interactive.container import Container
    from osp.core.session.session import Session
    from osp.core.session.wrapper import Wrapper


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

    @label.setter
    def label(self, value: str) -> None:
        """Replace the preferred label of this entity.

        When such preferred label does not exist, it is created.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        language = self.label_literal.language \
            if self.label_literal is not None else None
        self.label_literal = Literal(value, lang=language) \
            if value is not None else None

    @property
    def label_lang(self) -> Optional[str]:
        """Get the language of the preferred label of this entity.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        return self.label_literal.language \
            if self.label_literal is not None else None

    @label_lang.setter
    def label_lang(self, value: str) -> None:
        """Set the language of the preferred label of this entity.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        self.label_literal = Literal(self.label_literal, lang=value)

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
        value.update(self)
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
        labels = self._sort_labels_and_properties_by_preference(labels)
        # Return the first label
        return labels[0][0] if len(labels) > 0 else None

    @label_literal.setter
    def label_literal(self, value: Optional[Literal]) -> None:
        """Replace the preferred label for this entity.

        The labels are first sorted by the property defining them (which is
        an attribute of the session that this entity is stored on), and then by
        their length.

        Args:
            value: the preferred label to replace the current one with. If
                None, then all labels for this entity are deleted.
        """
        labels = self.iter_labels(return_literal=True,
                                  return_prop=True)
        labels = self._sort_labels_and_properties_by_preference(labels)

        preferred_label = labels[0] if len(labels) > 0 else None

        # Label deletion.
        if value is None:
            for label_prop in self.session.label_properties:
                self.session.graph.remove((self.identifier,
                                           label_prop,
                                           None))
        elif preferred_label is not None:
            self.session.graph.remove((self.identifier,
                                       preferred_label[1],
                                       preferred_label[0]))

        # Label creation.
        if value is not None:
            if preferred_label is not None:
                self.session.graph.add((self.identifier,
                                        preferred_label[1],
                                        value))
            else:
                self.session.graph.add((self.identifier,
                                        self.session.label_properties[0],
                                        value))

    def _sort_labels_and_properties_by_preference(
            self,
            labels: Iterator[Tuple[Literal, URIRef]]) \
            -> List[Tuple[Literal, URIRef]]:
        """Sort the labels for this entity in order of preference.

        The labels are first sorted by the property defining them (which is
        an attribute of the session that this entity is stored on),
        then by their language, and then by their length.

        Args:
            labels: an iterator of tuples where the first element is an
                assigned label literal (the label) and the second one the
                property used for this assignment.
        """
        # Sort by label property preference, and length.
        labels = sorted(
            labels,
            key=lambda x:
            (self.session.label_properties.index(x[1]),
             (self.session.label_languages + ('en', None, x[0].language))
             .index(x[0].language),
             len(x[0])))
        return labels

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
        """Get the all the triples where the entity is the subject."""
        if self.__graph is not None:
            return set(self.__graph.triples((None, None, None)))
        else:
            return set(self.session.graph.triples((self.identifier, None,
                                                   None)))

    @property
    def graph(self) -> Graph:
        """Graph where the ontology entity's data lives."""
        return self.session.graph if self.session is not None else self.__graph

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
                 session: Optional[Union['Session',
                                         'Container',
                                         'Wrapper']] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False) -> None:
        """Initialize the ontology entity.

        Args:
            uid: UID identifying the entity.
            session: Session where the entity is stored.
            triples: Construct the entity with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
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

        from osp.core.session.wrapper import Wrapper
        if session is None:
            from osp.core.ontology.interactive.container import Container
            from osp.core.session.session import Session
            environment = Container.get_current_container_context() or \
                Session.get_default_session()
            with environment:
                session = Session.get_default_session()
            if isinstance(environment, Container):
                environment.connect(self.identifier)
        elif isinstance(session, Wrapper):
            session = session.session
        if self.__graph is not None:
            # Only change what is stored in the session if custom triples were
            # provided.
            if not merge:
                session.update(self)
            else:
                session.merge(self)
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

    def __bool__(self):
        """Returns the boolean value of the entity, always true."""
        return True
