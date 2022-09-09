"""Abstract superclass of any entity in the ontology."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from rdflib import Graph, Literal, URIRef
from rdflib.term import Identifier

from simphony_osp.utils.cache import lru_cache_timestamp
from simphony_osp.utils.datatypes import UID, Triple

if TYPE_CHECKING:
    from simphony_osp.ontology.namespace import OntologyNamespace
    from simphony_osp.ontology.operations.container import Container
    from simphony_osp.session.session import Session
    from simphony_osp.session.wrapper import Wrapper

logger = logging.getLogger(__name__)


class OntologyEntity(ABC):
    """Abstract superclass of any entity in ontology entity."""

    rdf_type: Optional[Union[URIRef, Set[URIRef]]] = None
    rdf_identifier: Type

    # Public API
    # ↓ ------ ↓

    @property
    def iri(self) -> URIRef:
        """IRI of the Entity.

        Raises:
            TypeError: When the identifier of the ontology entity is not an
                IRI.
        """
        return self.uid.to_iri()

    @property
    def identifier(self) -> Identifier:
        """Semantic web resource identifying the entity.

        Usually an URIRef or BNode.
        """
        return self.uid.to_identifier()

    @property
    def label(self) -> Optional[str]:
        """Get the preferred label of this entity, if it exists.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        label_literal = self.label_literal
        return str(label_literal) if label_literal is not None else None

    @label.setter
    def label(self, value: str) -> None:
        """Replace the preferred label of this entity.

        When such preferred label does not exist, it is created.

        See the docstring for `label_literal` for more information on the
        definition of preferred label.
        """
        label_literal = self.label_literal
        language = (
            label_literal.language if label_literal is not None else None
        )
        self.label_literal = (
            Literal(value, lang=language) if value is not None else None
        )

    @property
    def label_lang(self) -> Optional[str]:
        """Get the language of the main label of this entity.

        See the docstring for `label_literal` for more information on the
        definition of main label.
        """
        label_literal = self.label_literal
        return label_literal.language if label_literal is not None else None

    @label_lang.setter
    def label_lang(self, value: str) -> None:
        """Set the language of the main label of this entity.

        See the docstring for `label_literal` for more information on the
        definition of main label.
        """
        self.label_literal = Literal(self.label_literal, lang=value)

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def namespace(self) -> Optional[OntologyNamespace]:
        """Return the ontology namespace to which this entity is associated."""
        return next((x for x in self.session.namespaces if self in x), None)

    @property
    def session(self) -> Session:
        """The session where the entity is stored."""
        return self._session

    @session.setter
    def session(self, value: Session) -> None:
        """Change the session where the entity is stored.

        Equivalent to removing the item from the previous session and adding it
        to the new session.
        """
        value.update(self)
        if self._session is not value:
            self._session.delete(self)
        self._session = value

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def direct_superclasses(
        self: ONTOLOGY_ENTITY,
    ) -> FrozenSet[ONTOLOGY_ENTITY]:
        """Get the direct superclasses of the entity.

        Returns:
            The direct superclasses of the entity.
        """
        return frozenset(self._get_direct_superclasses())

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def direct_subclasses(self: ONTOLOGY_ENTITY) -> FrozenSet[ONTOLOGY_ENTITY]:
        """Get the direct subclasses of the entity.

        Returns:
            The direct subclasses of the entity.
        """
        return frozenset(self._get_direct_subclasses())

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def superclasses(self: ONTOLOGY_ENTITY) -> FrozenSet[ONTOLOGY_ENTITY]:
        """Get the superclass of the entity.

        Returns:
            The superclasses of the entity.

        """
        return frozenset(self._get_superclasses())

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def subclasses(self: ONTOLOGY_ENTITY) -> FrozenSet[ONTOLOGY_ENTITY]:
        """Get the subclasses of the entity.

        Returns:
            The subclasses of the entity

        """
        return frozenset(self._get_subclasses())

    def is_superclass_of(self, other: OntologyEntity) -> bool:
        """Perform a superclass check.

        Args:
            other: The other ontology entity.

        Returns:
            Whether self is a superclass of the other other entity.
        """
        return self in other.superclasses

    def is_subclass_of(self, other: OntologyEntity) -> bool:
        """Perform a subclass check.

        Args:
            other: The other entity.

        Returns:
            bool: Whether self is a subclass of the other entity.

        """
        return self in other.subclasses

    def __eq__(self, other: OntologyEntity) -> bool:
        """Check whether two entities are the same.

        Two entities are considered equal when they have the same identifier
        and are stored in the same session.

        Args:
            other: The other entity.

        Returns:
            Whether the two entities are the same.
        """
        # TODO: Blank nodes with different IDs.
        return (
            isinstance(other, OntologyEntity)
            and self.session == other.session
            and self.identifier == other.identifier
        )

    def __bool__(self):
        """Returns the boolean value of the entity, always true."""
        return True

    def iter_labels(
        self,
        lang: Optional[str] = None,
        return_prop: bool = False,
        return_literal: bool = True,
    ) -> Iterator[
        Union[Literal, str, Tuple[str, URIRef], Tuple[Literal, URIRef]]
    ]:
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
        return self.session.iter_labels(
            entity=self,
            lang=lang,
            return_literal=return_literal,
            return_prop=return_prop,
        )

    @property
    def label_literal(self) -> Optional[Literal]:
        """Get the main label for this entity.

        The labels are first sorted by the property defining them, then by
        their language, and then by their length.

        Returns:
            The first label in the resulting ordering is returned. If the
            entity has no label, then None is returned.
        """
        labels = self.iter_labels(return_literal=True, return_prop=True)
        labels = self._sort_labels_and_properties_by_preference(labels)
        # Return the first label
        return labels[0][0] if len(labels) > 0 else None

    @label_literal.setter
    def label_literal(self, value: Optional[Literal]) -> None:
        """Replace the main label for this entity.

        The labels are first sorted by the property defining them (which is
        an attribute of the session that this entity is stored on), and then by
        their length.

        Args:
            value: the main label to replace the current one with. If
                None, then all labels for this entity are deleted.
        """
        labels = self.iter_labels(return_literal=True, return_prop=True)
        labels = self._sort_labels_and_properties_by_preference(labels)

        main_label = labels[0] if len(labels) > 0 else None

        # Label deletion.
        if value is None:
            for label_prop in self.session.label_predicates:
                self.session.graph.remove((self.identifier, label_prop, None))
        elif main_label is not None:
            self.session.graph.remove(
                (self.identifier, main_label[1], main_label[0])
            )

        # Label creation.
        if value is not None:
            if main_label is not None:
                self.session.graph.add((self.identifier, main_label[1], value))
            else:
                self.session.graph.add(
                    (self.identifier, self.session.label_predicates[0], value)
                )

    @property
    def triples(self) -> Set[Triple]:
        """Get the all the triples where the entity is the subject.

        Triples from the underlying RDFLib graph where the entity is stored
        in which the entity's identifier is the subject.
        """
        if self.__graph is not None:
            return set(self.__graph.triples((None, None, None)))
        else:
            return set(
                self.session.graph.triples((self.identifier, None, None))
            )

    # ↑ ------ ↑
    # Public API

    @property
    def uid(self) -> UID:
        """Get a SimPhoNy identifier for this entity.

        The SimPhoNy identifier is known as UID. An UID is a Python class
        defined in SimPhoNy and can always be converted to a semantic web
        identifier.
        """
        return self._uid

    @property
    def graph(self) -> Graph:
        """Graph where the ontology entity's data lives."""
        return self.session.graph if self.session is not None else self.__graph

    __graph: Optional[Graph] = None  # Only exists during initialization.

    def __hash__(self) -> int:
        """Make the entity hashable."""
        return hash((self._uid, self.session))

    def __str__(self) -> str:
        """Transform the entity into a human-readable string."""
        return (
            f"{self.label}"
            if hasattr(self, "label") and self.label is not None
            else f"{self._uid}"
        )

    def __repr__(self) -> str:
        """Transform the entity into a string."""
        header = f"{self.__class__.__name__}"
        elements = [
            f"{self.label}"
            if hasattr(self, "label") and self.label is not None
            else None,
            f"{self.uid}",
        ]
        elements = filter(lambda x: x is not None, elements)
        return f"<{header}: {' '.join(elements)}>"

    def _sort_labels_and_properties_by_preference(
        self, labels: Iterator[Tuple[Literal, URIRef]]
    ) -> List[Tuple[Literal, URIRef]]:
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
            key=lambda x: (
                self.session.label_predicates.index(x[1]),
                (
                    self.session.label_languages + ("en", None, x[0].language)
                ).index(x[0].language),
                len(x[0]),
            ),
        )
        return labels

    @abstractmethod
    def _get_direct_superclasses(
        self: ONTOLOGY_ENTITY,
    ) -> Iterable[ONTOLOGY_ENTITY]:
        """Direct superclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def _get_direct_subclasses(
        self: ONTOLOGY_ENTITY,
    ) -> Iterable[ONTOLOGY_ENTITY]:
        """Direct subclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def _get_superclasses(self: ONTOLOGY_ENTITY) -> Iterable[ONTOLOGY_ENTITY]:
        """Superclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def _get_subclasses(self: ONTOLOGY_ENTITY) -> Iterable[ONTOLOGY_ENTITY]:
        """Subclass getter specific to the type of ontology entity."""
        pass

    @abstractmethod
    def __init__(
        self,
        uid: UID,
        session: Optional[Union[Session, Container, Wrapper]] = None,
        triples: Optional[Iterable[Triple]] = None,
        merge: Optional[bool] = False,
    ) -> None:
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
            raise Exception(
                f"Tried to initialize an ontology entity with "
                f"uid {uid}, which is not a UID object."
            )
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
                    raise ValueError(
                        "Trying to add extra triples to an "
                        "ontology entity with a subject that "
                        "does not match the individual's "
                        "identifier."
                    )
                self.__graph.add((s, p, o))

        from simphony_osp.session.wrapper import Wrapper

        if session is None:
            from simphony_osp.ontology.operations.container import (
                ContainerEnvironment,
            )
            from simphony_osp.session.session import Environment, Session

            environment = Environment.get_default_environment()
            session = Session.get_default_session()
            if isinstance(environment, ContainerEnvironment):
                environment.connect(self.identifier)
        elif isinstance(session, Wrapper):
            session = session.session
        if self.__graph is not None:
            # Only change what is stored in the session if custom triples were
            # provided.
            if merge is False:
                session.update(self)
            elif merge is True:
                session.merge(self)
            # Otherwise, it is None -> do not change what is stored.
        self._session = session
        self.__graph = None


ONTOLOGY_ENTITY = TypeVar("ONTOLOGY_ENTITY", bound=OntologyEntity)
