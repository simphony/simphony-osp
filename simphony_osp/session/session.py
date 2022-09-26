"""Abstract Base Class for all Sessions."""
from __future__ import annotations

import itertools
import logging
from datetime import datetime
from functools import lru_cache, wraps
from inspect import isclass
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
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

from rdflib import OWL, RDF, RDFS, SKOS, BNode, Graph, Literal, URIRef
from rdflib.graph import ModificationException, ReadOnlyGraphAggregate
from rdflib.plugins.sparql.processor import SPARQLResult
from rdflib.query import ResultRow
from rdflib.term import Identifier, Node, Variable

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import (
    MultipleResultsError,
    OntologyIndividual,
    ResultEmptyError,
)
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.ontology.utils import DataStructureSet, compatible_classes
from simphony_osp.utils import simphony_namespace
from simphony_osp.utils.cache import lru_cache_weak
from simphony_osp.utils.datatypes import (
    UID,
    AnnotationValue,
    AttributeValue,
    RelationshipValue,
    Triple,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simphony_osp.interfaces.interface import Interface, InterfaceDriver

ENTITY = TypeVar("ENTITY", bound=OntologyEntity)


RDF_type = RDF.type
OWL_inverseOf = OWL.inverseOf


class Environment:
    """Environment where ontology entities may be created.

    E.g. sessions, containers.
    """

    # ↓ --------------------- Public API --------------------- ↓ #

    @property
    def locked(self) -> bool:
        """Whether the environment is locked or not.

        A locked environment will not be closed when using it as a context
        manager and leaving the context. Useful for setting it as the
        default environment when it is not intended to close it afterwards.
        """
        return (self._lock + bool(self._user_lock)) > 0

    @locked.setter
    def locked(self, value: bool):
        """Lock or unlock an environment."""
        self._user_lock = value

    def __enter__(self):
        """Set this as the default environment."""
        self._stack_default_environment.append(self)
        self._environment_references.add(self)
        return self

    def __exit__(self, *args):
        """Set the default environment back to the previous default."""
        if self is not self._stack_default_environment[-1]:
            raise RuntimeError(
                "Trying to exit the an environment context "
                "manager which was not the last entered one."
            )
        self._stack_default_environment.pop()
        if (
            self not in self._stack_default_environment
            and not self.subscribers
            and not self.locked
        ):
            self.close()
        return False

    def close(self):
        """Close this environment."""
        for environment in self.subscribers:
            environment.close()
            self.subscribers.remove(environment)
        self._environment_references.remove(self)

    def __bool__(self) -> bool:
        """Evaluate the truth value of the environment.

        Such value is always true.
        """
        return True

    # ↑ --------------------- Public API --------------------- ↑ #

    _session_linked: Optional[Session] = None
    _stack_default_environment: List[Environment] = []
    _environment_references: Set[Environment] = set()

    _lock: int = 0
    """See the docstring of `locked` for an explanation of what locking an
    environment means."""

    _user_lock: bool = False
    """See the docstring of `locked` for an explanation of what locking an
    environment means.

    This property manages locks performed by the user (by setting the
    `locked` attribute).
    """

    def lock(self):
        """Increase the lock count.

        This way of locking is not meant to be used by end users, only
        internally within SimPhoNy code, as it allows to lock the
        environment several times, later requiring several unlocks, which is
        unintuitive.

        See the docstring of `locked` for an explanation of what locking an
        environment means.
        """
        self._lock += 1

    def unlock(self):
        """Decrease the lock count.

        This way of unlocking is not meant to be used by end users, only
        internally within SimPhoNy code, as it is the counterpart of
        `lock`, which allows to lock the environment several times,
        later requiring several unlocks, which is unintuitive.

        See the docstring of `locked` for an explanation of what locking an
        environment means.
        """
        self._lock = self._lock - 1 if self._lock > 0 else 0

    _subscribers: Set[Environment]
    """A private attribute is used in order not to interfere with the
    `__getattr__`method from OntologyIndividual."""

    def __init__(self, *args, **kwargs):
        """Initialize the environment with an empty set of subscribers."""
        self._subscribers = set()
        super().__init__(*args, **kwargs)

    @property
    def subscribers(self) -> Set[Environment]:
        """Environments that depend on this instance.

        Such environments will be closed when this instance is closed.
        """
        return self._subscribers

    @subscribers.setter
    def subscribers(self, value: Set[Environment]):
        """Setter for the private  `_subscribers` attribute."""
        self._subscribers = value

    @classmethod
    def get_default_environment(cls) -> Optional[Environment]:
        """Returns the default environment."""
        for environment in cls._stack_default_environment[::-1]:
            return environment
        else:
            return None


class SessionSet(DataStructureSet):
    """A set interface to a session.

    This class looks like and acts like the standard `set`, but it is an
    interface to the methods from `Session` that manage the addition and
    removal of individuals.
    """

    _session: Session

    def __init__(
        self,
        session: Optional[Session] = None,
        oclass: Optional[OntologyClass] = None,
        uids: Optional[Iterable[UID]] = None,
    ):
        """Fix the linked session, the class and the identifier filter."""
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError(
                "Found object of type %s passed to argument "
                "oclass. Should be an OntologyClass." % type(oclass)
            )
        uids = tuple(uids) if uids is not None else None
        if uids is not None:
            for uid in uids:
                if not isinstance(uid, UID):
                    raise TypeError(
                        "Found object of type %s. Should be an UID."
                        % type(uid)
                    )

        self._class_filter = oclass
        self._uid_filter = uids
        self._session = session or Session.get_default_session()
        super().__init__()

    def __iter__(self):
        """The entities contained in the session."""
        identifiers = self._uid_filter
        class_ = self._class_filter

        if identifiers:
            yielded = set()
            for entity in self._iter_identifiers():
                if entity not in yielded:
                    yield entity
        elif class_:
            yield from (
                row[0]
                for row in self._session.sparql(
                    f"""
                    SELECT DISTINCT ?entity WHERE {{
                        ?entity rdf:type/rdfs:subClassOf*
                        <{class_.iri}> .
                    }}
                """,
                    ontology=True,
                )(entity=OntologyIndividual)
            )
        else:
            yield from iter(self._session)

    def __contains__(self, item: OntologyIndividual) -> bool:
        """Check whether an ontology entity belongs to the session."""
        return item in self._session and (
            item.is_a(self._class_filter) if self._class_filter else True
        )

    def update(self, other: Iterable[OntologyIndividual]) -> None:
        """Update the set with the union of itself and others."""
        other = set(other)
        if self._class_filter:
            for individual in other:
                if not individual.is_a(self._class_filter):
                    raise RuntimeError(
                        f"Cannot update {self} with {individual} because it "
                        f"does not belong to class {self._class_filter}."
                    )

        self._session.add(
            *other,
            merge=True,
            exists_ok=True,
        )

    def intersection_update(self, other: Iterable[OntologyIndividual]) -> None:
        """Update the set with the intersection of itself and another."""
        intersection = set(
            x
            for x in other
            if (x.identifier, RDF.type, None) in self._session.graph
        )

        if self._class_filter:
            for individual in intersection:
                if not individual.is_a(self._class_filter):
                    raise RuntimeError(
                        f"Cannot update {self} with {individual} because it "
                        f"does not belong to class {self._class_filter}."
                    )

        existing = set(
            x.identifier for x in self._session.get(oclass=self._class_filter)
        )
        remove = existing - set(x.identifier for x in intersection)

        self._session.add(
            *intersection,
            merge=True,
            exists_ok=True,
        )
        self._session.delete(remove)

    def difference_update(self, other: Iterable[OntologyIndividual]) -> None:
        """Remove all elements of another set from this set."""
        other = set(other)
        exists = set()
        for entity in other:
            try:
                exists.add(
                    self._session.from_identifier_typed(
                        entity.identifier, typing=OntologyIndividual
                    )
                )
            except KeyError:
                pass

        if self._class_filter:
            for individual in exists:
                if not individual.is_a(self._class_filter):
                    raise RuntimeError(
                        f"Cannot delete {individual} because it "
                        f"does not belong to class {self._class_filter}."
                    )

        self._session.delete(exists)

    def symmetric_difference_update(
        self, other: Iterable[OntologyIndividual]
    ) -> None:
        """Update set with the symmetric difference of it and another."""
        other = set(other)
        intersection = set(
            x
            for x in other
            if (x.identifier, RDF.type, None) in self._session.graph
        )
        add = other - intersection
        delete = set(
            x
            for x in self
            if x.identifier in (x.identifier for x in intersection)
        )

        if self._class_filter:
            for individual in add:
                if not individual.is_a(self._class_filter):
                    raise RuntimeError(
                        f"Cannot add {individual} because it "
                        f"does not belong to class {self._class_filter}."
                    )
            for individual in delete:
                if not individual.is_a(self._class_filter):
                    raise RuntimeError(
                        f"Cannot delete {individual} because it "
                        f"does not belong to class {self._class_filter}."
                    )

        self._session.add(add, merge=False, exists_ok=False)
        self._session.delete(delete)

    def __repr__(self) -> str:
        """Return repr(self)."""
        return (
            set(self).__repr__()
            + " <"
            + (
                f"class {self._class_filter} "
                if self._class_filter is not None
                else ""
            )
            + f"of session {self._session.identifier or self._session}>"
        )

    def one(
        self,
    ) -> OntologyIndividual:
        """Return one element.

        Return one element if the set contains one element, else raise
        an exception.

        Returns:
            The only element contained in the set.

        Raises:
            ResultEmptyError: No elements in the set.
            MultipleResultsError: More than one element in the set.
        """
        iter_self = iter(self)
        first_element = next(iter_self, StopIteration)
        if first_element is StopIteration:
            raise ResultEmptyError("No elements to be yielded.")
        second_element = next(iter_self, StopIteration)
        if second_element is not StopIteration:
            raise MultipleResultsError("More than one element can be yielded.")
        return first_element

    def any(
        self,
    ) -> Optional[Union[AnnotationValue, AttributeValue, RelationshipValue]]:
        """Return any element of the set.

        Returns:
            Any element from the set if the set is not empty, else None.
        """
        return next(iter(self), None)

    def all(self) -> SessionSet:
        """Return all elements from the set.

        Returns:
            All elements from the set, namely the set itself.
        """
        return self

    def _iter_identifiers(self) -> Iterator[Optional[OntologyIndividual]]:
        identifiers = self._uid_filter
        class_ = self._class_filter
        for i, identifier in identifiers:
            try:
                entity = self._session.from_identifier_typed(
                    identifier, OntologyIndividual
                )
            except KeyError:
                entity = None
            if entity and class_ and not entity.is_a(class_):
                entity = None
            yield entity


class Session(Environment):
    """'Box' that stores ontology individuals."""

    # ↓ --------------------- Public API --------------------- ↓ #
    """These methods are meant to be available to the end-user."""

    identifier: Optional[str] = None
    """A label for the session.

    The identifier is just a label for the session to be displayed within
    Python (string representation of the session). It has no other effect.
    """

    def commit(self) -> None:
        """Commit pending changes to the session's graph."""
        self._graph.commit()
        # if self.ontology is not self:
        #    self.ontology.commit()
        self.creation_set = set()

    def compute(self, **kwargs) -> None:
        """Run simulations on supported graph stores."""
        from simphony_osp.interfaces.remote.client import RemoteStoreClient

        if self._driver is not None:
            self.commit()
            self._driver.compute(**kwargs)
        elif isinstance(self._graph.store, RemoteStoreClient):
            self._graph.store.execute_method("compute")
        else:
            raise AttributeError(
                f"Session {self} is not attached to a "
                f"simulation engine. Thus, the attribute "
                f"`compute` is not available."
            )

    def close(self) -> None:
        """Close the connection to the session's backend.

        Sessions are an interface to a graph linked to an RDFLib store (a
        backend). If the session will not be used anymore, then it makes
        sense to close the connection to such backend to free resources.
        """
        if self in self._stack_default_environment:
            raise RuntimeError(
                "Cannot close a session that is currently "
                "being used as a context manager."
            )
        super().close()
        self.graph.close(commit_pending_transaction=False)

    def sparql(self, query: str, ontology: bool = False) -> QueryResult:
        """Perform a SPARQL CONSTRUCT, DESCRIBE, SELECT or ASK query.

        By default, the query is performed only on the session's data (the
        ontology is not included).

        Args:
            query: String to use as query.
            ontology: Whether to include the ontology in the query or not.
                When the ontology is included, only read-only queries are
                possible.
        """
        graph = (
            self.graph
            if not ontology
            else ReadOnlyGraphAggregate([self.graph, self.ontology.graph])
        )
        result = graph.query(query)
        return QueryResult(
            {
                "type_": result.type,
                "vars_": result.vars,
                "bindings": result.bindings,
                "askAnswer": result.askAnswer,
                "graph": result.graph,
            },
            session=self,
        )

    def __enter__(self):
        """Sets the session as the default session."""
        super().__enter__()
        self.creation_set = set()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restores the previous default session."""
        return super().__exit__(exc_type, exc_val, exc_tb)

    def __contains__(self, item: OntologyEntity):
        """Check whether an ontology entity is stored on the session."""
        return item.session is self

    def __iter__(self) -> Iterator[OntologyEntity]:
        """Iterate over all the ontology entities in the session.

        Be careful when using this operation, as it can be computationally very
        expensive.
        """
        # Warning: entities can be repeated.
        return (
            self.from_identifier(identifier)
            for identifier in self.iter_identifiers()
        )

    def __len__(self) -> int:
        """Return the number of ontology entities within the session."""
        return sum(1 for _ in self)

    @lru_cache_weak(maxsize=4096)
    # On `__init__.py` there is an option to bypass this cache when the
    # session is not a T-Box.
    def from_label(
        self,
        label: str,
        lang: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> FrozenSet[OntologyEntity]:
        """Get an ontology entity from its label.

        Args:
            label: The label of the ontology entity.
            lang: The language of the label.
            case_sensitive: when false, look for similar labels with
                different capitalization.

        Raises:
            KeyError: Unknown label.

        Returns:
            The ontology entity.
        """
        results = set()

        identifiers_and_labels = self.iter_labels(
            lang=lang,
            return_prop=False,
            return_literal=False,
            return_identifier=True,
        )
        if case_sensitive is False:
            comp_label = label.lower()
            identifiers_and_labels = (
                (label.lower(), identifier)
                for label, identifier in identifiers_and_labels
            )
        else:
            comp_label = label

        identifiers_and_labels = (
            (label, identifier)
            for label, identifier in identifiers_and_labels
            if label == comp_label
        )

        for _, identifier in identifiers_and_labels:
            try:
                results.add(self.from_identifier(identifier))
            except KeyError:
                pass
        if len(results) == 0:
            error = "No element with label %s was found in ontology %s." % (
                label,
                self,
            )
            raise KeyError(error)

        return frozenset(results)

    def add(
        self,
        *individuals: Union[OntologyIndividual, Iterable[OntologyIndividual]],
        merge: bool = False,
        exists_ok: bool = False,
        all_triples: bool = False,
    ) -> Union[OntologyIndividual, FrozenSet[OntologyIndividual]]:
        """Copies ontology individuals to the session.

        Args:
            individuals: Ontology individuals to add to this session.
            merge: Whether to merge individuals with existing ones if their
                identifiers match (read the SimPhoNy documentation for more
                details).
            exists_ok: Merge or overwrite individuals when they already exist
                in the session rather than raising an exception.
            all_triples: When an individual is added to the session, SimPhoNy
                only copies the details that are relevant from an ontological
                point of view: the individual's attributes, the classes it
                belongs to, and its connections to other ontology individuals
                that are also being copied at the same time.

                However, in some cases, it is necessary to keep all the
                information about the individual, even if it cannot be
                understood by SimPhoNy. Set this option to `True` to copy all
                RDF statements describing the individual, that is, all RDF
                statements where the individual is the subject.

                One example of a situation where this option is useful is
                when the individual is attached through an object property to
                another one which is not properly defined (i.e. has no type
                assigned). This situation commonly arises when using the
                `dcat:accessURL` object property.

        Returns:
            The new copies of the individuals.

        Raises:
            RuntimeError: The individual being added has an identifier that
            matches the identifier of an individual that already exists in the
            session.
        """
        # Unpack iterables
        individuals = list(
            individual
            for x in individuals
            for individual in (
                x if not isinstance(x, OntologyIndividual) else (x,)
            )
        )
        # Get the identifiers of the individuals
        identifiers = list(individual.identifier for individual in individuals)
        # Get a list of files within the individuals to add
        files = {
            individual
            for individual in individuals
            if set(class_.identifier for class_ in individual.superclasses)
            & {simphony_namespace.File}
            and individual.session is not self
        }

        # Paste the individuals
        """The attributes of the individuals are always kept. The
        relationships between the individuals are only kept when they are
        pasted together.
        """
        if (
            any(
                (identifier, None, None) in self.graph
                for identifier in identifiers
            )
            and exists_ok is False
        ):
            raise RuntimeError(
                "Some of the added entities already exist on the session."
            )
        elif (
            merge
            and files
            and any(
                (identifier, None, None) in self.graph
                for identifier in {x.identifier for x in files}
            )
        ):
            raise RuntimeError(
                "Some of the added file entities already exist on the "
                "session. File entities cannot be merged with existing ones."
            )
        delete = (
            (individual.identifier, None, None)
            for individual in individuals
            if individual.session is not self
        )

        @lru_cache(maxsize=4096)
        def is_known(
            p: Node,
        ) -> Optional[
            Union[OntologyAttribute, OntologyRelationship, OntologyAnnotation]
        ]:
            """Check whether a predicate is known in the session's ontology.

            Args:
                p: Predicate to be evaluated.

            Returns:
                The predicate if it is known, `None` if it is not.
            """
            try:
                entity = self.ontology.from_identifier(p)
                if not isinstance(
                    entity,
                    (
                        OntologyRelationship,
                        OntologyAttribute,
                        OntologyAnnotation,
                    ),
                ):
                    entity = None
            except KeyError:
                entity = None
            return entity

        def is_valid(
            s: Node, p: Node, o: Node, exception: bool = False
        ) -> bool:
            """Check whether a predicate is known and has a valid target.

               Check whether the predicate is a known relationship, attribute
               or annotation in this session's ontology, and points to a
               "valid" target:
               - Attributes must point to literals.
               - Relationships must point to individuals being copied
                 simultaneously into the session.
               - Annotations can point to anything.

               The word "valid" is written with quotation marks because it is
               arguably just a superset of what is really valid (e.g. it is
               not checked that the data type of literals match the range of
               the attributes).

            Args:
                s: Subject of the statement.
                p: Predicate to be evaluated.
                o: Target of the predicate.
                exception: When a value is given, an exception instead of a
                    warning is emitted if an "invalid" target is identified.
                    The value is used to identify the ontology individual is
                    related to.

            Returns:
                The predicate points to a "valid" target.
            """
            predicate = is_known(p)
            if isinstance(predicate, OntologyAttribute):
                result = isinstance(o, Literal)
            elif isinstance(predicate, OntologyRelationship):
                result = o in identifiers
            elif isinstance(predicate, OntologyAnnotation):
                result = True
            else:  # isinstance(predicate, type(None)):
                result = False

            if not result:
                if not predicate:
                    text = (
                        f"Individual {s} is the subject of a statement "
                        f"that has {p} as predicate, which does not match any "
                        f"annotation, relationship or attribute from the "
                        f"installed ontologies."
                    )
                elif isinstance(predicate, OntologyAttribute):
                    text = (
                        f"Individual {s} is the subject of a RDF "
                        f"statement that has {predicate} as predicate. "
                        f"{predicate} is an ontology attribute, but "
                        f"the object of the statement "
                        f"is not a literal."
                    )
                else:
                    text = ""

                if text:
                    if exception:
                        raise RuntimeError(
                            text + " Set the keyword argument `all_triples`"
                            "to `True` to ignore this error."
                        )
                    else:
                        logger.warning(
                            "Accepting uninterpretable RDF statement: " + text
                        )

            return result

        add = (
            (s, p, o)
            for individual in individuals
            for s, p, o in individual.session.graph.triples(
                (individual.identifier, None, None)
            )
            if (
                p == RDF.type
                or is_valid(s, p, o, exception=not all_triples)
                or all_triples
            )
        )
        if not merge:
            """Replace previous individuals if merge is False."""
            for pattern in delete:
                self.graph.remove(pattern)
        self.graph.addN((s, p, o, self.graph) for s, p, o in add)
        files = ((file.identifier, file.operations.handle) for file in files)
        for identifier, contents in files:
            self.from_identifier_typed(
                identifier, typing=OntologyIndividual
            ).operations.overwrite(contents)
        added_objects = list(
            self.from_identifier_typed(identifier, typing=OntologyIndividual)
            for identifier in identifiers
        )
        return (
            next(iter(added_objects), None)
            if len(added_objects) <= 1
            else added_objects
        )

    def delete(
        self,
        *entities: Union[
            Union[OntologyEntity, Identifier],
            Iterable[Union[OntologyEntity, Identifier]],
        ],
    ):
        """Remove ontology individuals from the session.

        Args:
            entities: Ontology individuals to remove from the session. It is
                also possible to just provide their identifiers.

        Raises:
            ValueError: When at least one of the given ontology individuals is
                not contained in the session.
        """
        entities = frozenset(
            entity
            for x in entities
            for entity in (
                x if not isinstance(x, (OntologyEntity, Identifier)) else (x,)
            )
        )

        for entity in entities:
            if isinstance(entity, OntologyEntity) and entity not in self:
                raise ValueError(f"Entity {entity} not contained in {self}.")

        for entity in entities:
            if isinstance(entity, OntologyEntity):
                entity = entity.identifier
            self._track_identifiers(entity, delete=True)
            self._graph.remove((entity, None, None))
            self._graph.remove((None, None, entity))

    def clear(self, force: bool = False):
        """Clear all the data stored in the session.

        Args:
            force: Try to clear read-only sessions too.
        """
        graph = self._graph_writable if force else self._graph
        graph.remove((None, None, None))
        self._namespaces.clear()
        self.entity_cache_timestamp = datetime.now()
        self.from_identifier.cache_clear()
        self.from_label.cache_clear()

        # Reload the essential TBox required by ontologies.
        if self.ontology is self:
            for parser in (
                OntologyParser.get_parser("simphony"),
                OntologyParser.get_parser("owl"),
                OntologyParser.get_parser("rdfs"),
            ):
                self.ontology.load_parser(parser)

    def get(
        self,
        *individuals: Union[OntologyIndividual, Identifier, str],
        oclass: Optional[OntologyClass] = None,
    ) -> Union[
        Set[OntologyIndividual],
        Optional[OntologyIndividual],
        Tuple[Optional[OntologyIndividual]],
    ]:
        """Return the individuals in the session.

        The structure of the output can vary depending on the form used for
        the call. See the "Returns:" section of this
        docstring for more details on this.

        Note: If you are reading the SimPhoNy documentation API Reference, it
        is likely that you cannot read this docstring. As a workaround, click
        the `source` button to read it in its raw form.

        Args:
            individuals: Restrict the individuals to be returned to a certain
                subset of the individuals in the session.
            oclass: Only yield ontology individuals which belong to a subclass
                of the given ontology class. Defaults to None (no filter).

        Returns:
            Calls without `*individuals` (SessionSet): The result of the
                call is a set-like object. This corresponds to
                the calls `get()`, `get(oclass=___)`.
            Calls with `*individuals` (Optional[OntologyIndividual],
                    Tuple[Optional["OntologyIndividual"], ...]):
                The position of each element in the result is determined by the
                position of the corresponding identifier/individual in the
                given list of identifiers/individuals. In this case, the result
                can contain `None` values if a given identifier/individual is
                not in the session, or if it does not satisfy the class
                filter. This description corresponds to the calls
                `get(*individuals)`, `get(*individuals, oclass=`___`)`.

        Raises:
            TypeError: Objects that are not ontology individuals,
                identifiers or strings provided as positional arguments.
            TypeError: Object that is not an ontology class passed as
                keyword argument `oclass`.
            RuntimeError: Ontology individuals that belong to a different
                session provided.
        """
        identifiers = list(individuals)
        for i, x in enumerate(identifiers):
            if not isinstance(x, (OntologyIndividual, Identifier, str)):
                raise TypeError(
                    f"Expected {OntologyIndividual}, {Identifier} or {str} "
                    f"objects, not {type(x)}."
                )
            elif isinstance(x, OntologyIndividual) and x not in self:
                raise RuntimeError(
                    "Cannot get an individual that belongs to "
                    "a different session."
                )

            if isinstance(x, str):
                if not isinstance(x, Identifier):
                    identifiers[i] = URIRef(x)
            elif isinstance(x, OntologyIndividual):
                identifiers[i] = x.identifier

        if identifiers:
            entities = [None] * len(identifiers)
            for i, identifier in enumerate(identifiers):
                try:
                    entity = self.from_identifier(identifier)
                except KeyError:
                    entity = None
                if entity and oclass and not entity.is_a(oclass):
                    entity = None
                entities[i] = entity

            if len(identifiers) == 1:
                entities = entities[0]
            else:
                entities = tuple(entities)
        else:
            entities = SessionSet(session=self, oclass=oclass)

        return entities

    def iter(
        self,
        *individuals: Union[OntologyIndividual, Identifier, str],
        oclass: Optional[OntologyClass] = None,
    ) -> Union[
        Iterator[OntologyIndividual],
        Iterator[Optional[OntologyIndividual]],
    ]:
        """Iterate over the ontology individuals in the session.

        The structure of the output can vary depending on the form used for
        the call. See the "Returns:" section of this docstring for more
        details on this.

        Note: If you are reading the SimPhoNy documentation API Reference, it
        is likely that you cannot read this docstring. As a workaround, click
        the `source` button to read it in its raw form.

        Args:
            individuals: Restrict the individuals to be returned to a certain
                subset of the individuals in the session.
            oclass: Only yield ontology individuals which belong to a subclass
                of the given ontology class. Defaults to None (no filter).

        Returns:
            Calls without `*individuals` (Iterator[OntologyIndividual]): The
                position of each element in the result is non-deterministic.
                This corresponds to the calls `iter()`, `iter(oclass=___)`.
            Calls with `*individuals` (Iterator[Optional[
                    OntologyIndividual]]):
                The position of each element in the result is determined by the
                position of the corresponding identifier/individual in the
                given list of identifiers/individuals. In this case, the result
                can contain `None` values if a given identifier/individual is
                not in the session, or if it does not satisfy the class
                filter. This description corresponds to the calls
                `iter(*individuals)`, `iter(*individuals, oclass=`___`)`.

        Raises:
            TypeError: Objects that are not ontology individuals,
                identifiers or strings provided as positional arguments.
            TypeError: Object that is not an ontology class passed as
                keyword argument `oclass`.
            RuntimeError: Ontology individuals that belong to a different
                session provided.
        """
        identifiers = list(individuals)
        for i, x in enumerate(identifiers):
            if not isinstance(x, (OntologyIndividual, Identifier, str)):
                raise TypeError(
                    f"Expected {OntologyIndividual}, {Identifier} or {str} "
                    f"objects, not {type(x)}."
                )
            elif isinstance(x, OntologyIndividual) and x not in self:
                raise RuntimeError(
                    "Cannot get an individual that belongs to "
                    "a different session."
                )

            if isinstance(x, str):
                if not isinstance(x, Identifier):
                    identifiers[i] = URIRef(x)
            elif isinstance(x, OntologyIndividual):
                identifiers[i] = x.identifier

        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError(
                "Found object of type %s passed to argument "
                "oclass. Should be an OntologyClass." % type(oclass)
            )

        if identifiers:

            # The yield statement is encapsulated inside a function so that the
            # main function uses the return statement instead of yield. In this
            # way, exceptions are checked when the `iter` method is called
            # instead of when asking for the first result.
            def iterator() -> Iterator[Optional[OntologyIndividual]]:
                for identifier in identifiers:
                    try:
                        entity = self.from_identifier(identifier)
                    except KeyError:
                        entity = None
                    if entity and oclass and not entity.is_a(oclass):
                        entity = None
                    yield entity

            return iterator()

        else:
            return iter(SessionSet(session=self, oclass=oclass))

    # ↑ --------------------- Public API --------------------- ↑ #

    default_ontology: Session
    """The default ontology.

    When no T-Box is explicitly assigned to a session, this is the ontology
    it makes use of.
    """

    entity_cache_timestamp: Optional[datetime] = None
    """A timestamp marking the time when the session's graph was last modified.

    This timestamp is used by `OntologyEntity` and its subclasses to know
    whether they should invalidate their cache (e.g. the cache of the
    `superclasses` method must be invalidated when the session is cleared or a
    new ontology is loaded into the session).
    """

    @property
    def ontology(self) -> Session:
        """Another session considered to be the T-Box of this one.

        In a normal setting, a session is considered only to contain an A-Box.
        When it is necessary to look for a class, a relationship, an attribute
        or an annotation property, the session will look there for their
        definition.
        """
        return self._ontology or Session.default_ontology

    @ontology.setter
    def ontology(self, value: Optional[Session]) -> None:
        """Set the T-Box of this session."""
        if not isinstance(value, (Session, type(None))):
            raise TypeError(
                f"Expected {Session} or {type(None)}, not type {value}."
            )
        self._ontology = value

    _ontology: Optional[Session] = None
    """Private pointer to the T-Box of the session.

    Not `None` only when the T-Box of the session should be different from
    the default T-Box (the one referred to by the attribute `default_ontology`,
    which is by default a session containing all the installed ontologies).
    """

    label_predicates: Tuple[URIRef] = (SKOS.prefLabel, RDFS.label)
    """The identifiers of the RDF predicates to be considered as labels.

    The entity labels are used, for example, to be able to get ontology
    entities from namespace or session objects by such label.

    The order in which the properties are specified in the tuple matters. To
    determine the label of an object, the properties will be checked from
    left to right, until one of them is defined for that specific entity.
    This will be the label of such ontology entity. The rest of the
    properties to the right of such property will be ignored for that
    entity.

    For example, in the default case above, if an entity has an
    `SKOS.prefLabel` it will be considered to be its label, even if it also
    has an `RDFS.label`, which will be ignored. If another entity has no
    `SKOS.prefLabel` but has a `RDFS.label`, then the `RDFS.label` will
    define its label. This means that for some entity, one label property
    may be used while for another, a different property can be in use. If
    none of the properties are defined, then the entity is considered to
    have no label.
    """

    label_languages: Tuple[URIRef] = ("en",)
    # TODO: Set to user's language preference from the OS (users can usually
    #  set such a list in modern operating systems).
    """The preferred languages for the default label.

    Normally, entities will be available from all languages. However,
    in some places the label has to be printed. In such cases this default
    label will be used.

    When defining the label for an object as described in the
    `label_predicates` docstring above, this list will also be checked from
    left to right. When one of the languages specified is available,
    this will define the default label. Then the default label will default to
    english. If also not available, then any language will be used.
    """

    def __init__(
        self,
        base: Optional[Graph] = None,  # The graph must be OPEN already.
        driver: Optional[InterfaceDriver] = None,
        ontology: Optional[Union[Session, bool]] = None,
        identifier: Optional[str] = None,
        namespaces: Dict[str, URIRef] = None,
        from_parser: Optional[OntologyParser] = None,
    ):
        """Initializes the session.

        The keyword arguments are used internally by SimPhoNy and are not meant
        to be set manually.
        """
        super().__init__()
        self._environment_references.add(self)
        # Base the session graph either on a store if passed or an empty graph.
        if base is not None:
            self._graph_writable = base
            self._graph = base

        else:
            graph = Graph()
            self._graph_writable = graph
            self._graph = graph

        self._interface_driver = driver

        # Configure the ontology for this session
        if isinstance(ontology, Session):
            self.ontology = ontology
        elif ontology is True:
            self._graph = ReadOnlyGraphAggregate([self._graph_writable])
            self.ontology = self
        elif ontology is not None:
            raise TypeError(
                f"Invalid ontology argument: {ontology}."
                f"Expected either a {Session} or {bool} object, "
                f"got {type(ontology)} instead."
            )

        if self.ontology is not self:
            """Bypass cache if this session is not a T-Box"""

            def bypass_cache(method: Callable):
                wrapped_func = method.__wrapped__

                @wraps(wrapped_func)
                def bypassed(*args, **kwargs):
                    return wrapped_func(self, *args, **kwargs)

                bypassed.cache_clear = lambda: None
                return bypassed

            self.from_identifier = bypass_cache(self.from_identifier)
            self.from_label = bypass_cache(self.from_label)
        else:
            """Log the time of last entity cache clearing."""

            self.entity_cache_timestamp = datetime.now()

        self._entity_cache = dict()

        self.creation_set = set()
        self._storing = list()

        self._namespaces = dict()
        # Load the essential TBox required by ontologies.
        if self.ontology is self:
            for parser in (
                OntologyParser.get_parser("simphony"),
                OntologyParser.get_parser("owl"),
                OntologyParser.get_parser("rdfs"),
            ):
                self.ontology.load_parser(parser)
        if from_parser:  # Compute session graph from an ontology parser.
            if self.ontology is not self:
                raise RuntimeError(
                    "Cannot load parsers in sessions which "
                    "are not their own ontology. Load the "
                    "parser on the ontology instead."
                )
            if namespaces is not None:
                logger.warning(
                    f"Namespaces bindings {namespaces} ignored, "
                    f"as the session {self} is being created from "
                    f"a parser."
                )
            self.load_parser(from_parser)
            self.identifier = identifier or from_parser.identifier
        else:  # Create an empty session.
            self.identifier = identifier
            namespaces = namespaces if namespaces is not None else dict()
            for key, value in namespaces.items():
                self.bind(key, value)

    def __str__(self):
        """Convert the session to a string."""
        # TODO: Return the kind of RDFLib store attached too.
        return (
            f"<{self.__class__.__module__}.{self.__class__.__name__}: "
            f"{self.identifier if self.identifier is not None else ''} "
            f"at {hex(id(self))}>"
        )

    @lru_cache_weak(maxsize=4096)
    # On `__init__.py` there is an option to bypass this cache when the
    # session is not a T-Box.
    def from_identifier(self, identifier: Node) -> OntologyEntity:
        """Get an ontology entity from its identifier.

        Args:
            identifier: The identifier of the entity.

        Raises:
            KeyError: The ontology entity is not stored in this session.

        Returns:
            The OntologyEntity.
        """
        # WARNING: This method is a central point in SimPhoNy. Change with
        #  care.
        # TIP: Since the method is a central point in SimPhoNy, any
        #  optimization it gets will speed up SimPhoNy, while bad code in
        #  this method will slow it down.

        # Look for embedded classes.
        compatible = {
            rdf_type: compatible_classes(rdf_type, identifier)
            for rdf_type in self._graph.objects(identifier, RDF_type)
        }

        # If not an embedded class, then the type may be known in
        # the ontology. This means that an ontology individual would
        # have to be spawned.
        for rdf_type, found in compatible.items():
            if not found:
                try:
                    self.ontology.from_identifier(rdf_type)
                    found |= {OntologyIndividual}
                    break
                except KeyError:
                    pass

        compatible = set().union(*compatible.values())

        if (
            OntologyRelationship not in compatible
            and (identifier, OWL_inverseOf, None) in self._graph
        ):
            compatible |= {OntologyRelationship}

        """Some ontologies are hybrid RDFS and OWL ontologies (i.e. FOAF).
        In such cases, object and datatype properties are preferred to
        annotation properties."""
        if OntologyAnnotation in compatible and (
            compatible & {OntologyRelationship, OntologyAttribute}
        ):
            compatible.remove(OntologyAnnotation)

        """Finally return the single compatible class or raise an exception."""
        if len(compatible) >= 2:
            raise RuntimeError(
                f"Two or more python classes ("
                f"{', '.join(map(str, compatible))}) "
                f"could be spawned from {identifier}."
            )
        try:
            python_class = compatible.pop()
            return python_class(uid=UID(identifier), session=self, merge=None)
        except KeyError:
            raise KeyError(
                f"Identifier {identifier} does not match any OWL "
                f"entity, any entity natively supported by "
                f"SimPhoNy, nor an ontology individual "
                f"belonging to a class in the ontology."
            )

    def from_identifier_typed(
        self, identifier: Node, typing: Type[ENTITY]
    ) -> ENTITY:
        """Get an ontology entity from its identifier, enforcing a type check.

        Args:
            identifier: The identifier of the entity.
            typing: The expected type of the ontology entity matching the
                given identifier.

        Raises:
            KeyError: The ontology entity is not stored in this session.

        Returns:
            The OntologyEntity.
        """
        entity = self.from_identifier(identifier)
        if not isinstance(entity, typing):
            raise TypeError(f"{identifier} is not of class {typing}.")
        return entity

    def merge(self, entity: OntologyEntity) -> None:
        """Merge a given ontology entity with what is in the session.

        Copies the ontology entity to the session, but does not remove any
        old triples referring to the entity.

        Args:
            entity: The ontology entity to store.
        """
        self._update_and_merge_helper(entity, mode=False)

    def update(self, entity: OntologyEntity) -> None:
        """Store a copy of given ontology entity in the session.

        Args:
            entity: The ontology entity to store.
        """
        self._update_and_merge_helper(entity, mode=True)

    @property
    def namespaces(self) -> List[OntologyNamespace]:
        """Get all the namespaces bound to the session."""
        return [
            OntologyNamespace(iri=iri, name=name, ontology=self.ontology)
            for iri, name in self.ontology._namespaces.items()
        ]

    def bind(self, name: Optional[str], iri: Union[str, URIRef]):
        """Bind a namespace to this session.

        Args:
            name: the name to bind. The name is optional, a namespace object
                can be bound without name.
            iri: the IRI of the namespace to be bound to such name.
        """
        iri = URIRef(iri)
        for key, value in self.ontology._namespaces.items():
            if value == name and key != iri:
                raise ValueError(
                    f"Namespace {key} is already bound to name "
                    f"{name} in ontology {self}. "
                    f"Please unbind it first."
                )
        else:
            self.ontology._namespaces[iri] = name
            self.ontology._graph_writable.bind(name, iri)

    def unbind(self, name: Union[str, URIRef]):
        """Unbind a namespace from this session.

        Args:
            name: the name to which the namespace is already bound, or the
                IRI of the namespace.
        """
        for key, value in dict(self.ontology._namespaces).items():
            if value == name or key == URIRef(name):
                del self.ontology._namespaces[key]

    def get_namespace_bind(
        self, namespace: Union[OntologyNamespace, URIRef, str]
    ) -> Optional[str]:
        """Returns the name used to bind a namespace to the ontology.

        Args:
            namespace: Either an OntologyNamespace or the IRI of a namespace.

        Raises:
            KeyError: Namespace not bound to to the ontology.
        """
        ontology = self.ontology
        if isinstance(namespace, OntologyNamespace):
            ontology = namespace.ontology
            namespace = namespace.iri
        else:
            namespace = URIRef(namespace)

        not_bound_error = KeyError(
            f"Namespace {namespace} not bound to " f"ontology {self}."
        )
        if ontology is not self.ontology:
            raise not_bound_error
        try:
            return self.ontology._namespaces[namespace]
        except KeyError:
            raise not_bound_error

    def get_namespace(self, name: Union[str, URIRef]) -> OntologyNamespace:
        """Get a namespace registered with the session.

        Args:
            name: The namespace name or IRI to search for.

        Returns:
            The ontology namespace.

        Raises:
            KeyError: Namespace not found.
        """
        coincidences = iter(tuple())
        if isinstance(name, URIRef):
            coincidences_iri = (x for x in self.namespaces if x.iri == name)
            coincidences = itertools.chain(coincidences, coincidences_iri)
        elif isinstance(name, str):
            coincidences_name = (x for x in self.namespaces if x.name == name)
            coincidences = itertools.chain(coincidences, coincidences_name)
            # Last resort: user provided string but may be an IRI.
            coincidences_fallback = (
                x for x in self.namespaces if x.iri == URIRef(name)
            )
            coincidences = itertools.chain(coincidences, coincidences_fallback)

        result = next(coincidences, None)
        if result is None:
            raise KeyError(f"Namespace {name} not found in ontology {self}.")
        return result

    @property
    def graph(self) -> Graph:
        """Returns the session's graph."""
        return self._graph

    @property
    def driver(self) -> Optional[InterfaceDriver]:
        """The SimPhoNy interface on which the base graph is based on.

        Points to the interface response for realizing the base graph of the
        session. Not all graphs have to be based on an interface. In such
        cases, the value of this attribute is `None`.
        """
        return self._interface_driver

    @classmethod
    def get_default_session(cls) -> Optional[Session]:
        """Returns the default session."""
        for environment in cls._stack_default_environment[::-1]:
            if isinstance(environment, Session):
                return environment
        else:
            return None

    @classmethod
    def set_default_session(cls, session: Session):
        """Sets the first session of the stack of sessions.

        This effectively makes it the default. The method will not work if
        there are any other default environments in the stack
        """
        if len(cls._stack_default_environment) > 1:
            raise RuntimeError(
                "The default session cannot be changed when "
                "there are other environments in the stack."
            )
        try:
            cls._stack_default_environment.pop()
        except IndexError:
            pass
        cls._stack_default_environment.append(session)

    def load_parser(self, parser: OntologyParser):
        """Merge ontology packages with this ontology from a parser object.

        Args:
            parser: the ontology parser from where to load the new namespaces.
        """
        if self.ontology is not self:
            raise ModificationException()
        self._graph_writable += parser.graph
        for name, iri in parser.namespaces.items():
            self.bind(name, iri)
        self.entity_cache_timestamp = datetime.now()
        self.from_identifier.cache_clear()
        self.from_label.cache_clear()

    def iter_identifiers(self) -> Iterator[Union[BNode, URIRef]]:
        """Iterate over all the ontology entity identifiers in the session."""
        # Warning: identifiers can be repeated.
        supported_entity_types = frozenset(
            {
                # owl:AnnotationProperty
                OWL.AnnotationProperty,
                RDF.Property,
                # owl:DatatypeProperty
                OWL.DatatypeProperty,
                # owl:ObjectProperty
                OWL.ObjectProperty,
                # owl:Class
                OWL.Class,
                RDFS.Class,
                # owl:Restriction
                OWL.Restriction,
            }
        )

        # Yield the entities from the TBox (literals filtered out).
        if self.ontology is self:
            yield from (
                s
                for t in supported_entity_types
                for s in self.ontology.graph.subjects(RDF.type, t)
                if not isinstance(s, Literal)
            )

        # Yield the entities from the ABox (literals filtered out).
        yield from (
            t[0]
            for t in self._graph.triples((None, RDF.type, None))
            if not isinstance(t[0], Literal)
            and any(
                (t[2], RDF.type, supported_entity_type) in self.ontology.graph
                for supported_entity_type in supported_entity_types
            )
        )

    def iter_labels(
        self,
        entity: Optional[Union[Identifier, OntologyEntity]] = None,
        lang: Optional[str] = None,
        return_prop: bool = False,
        return_literal: bool = True,
        return_identifier: bool = False,
    ) -> Iterator[
        Union[
            Literal,
            str,
            Tuple[Union[Literal, str], Node],
            Tuple[Union[Literal, str], Node, Node],
        ]
    ]:
        """Iterate over all the labels of the entities in the session."""
        from simphony_osp.ontology.entity import OntologyEntity

        if isinstance(entity, OntologyEntity):
            entity = entity.identifier

        def filter_language(literal):
            if lang is None:
                return True
            elif lang == "":
                return literal.language is None
            else:
                return literal.language == lang

        labels = (
            (prop, literal, subject)
            for prop in self.label_predicates
            for subject, _, literal in self._graph.triples(
                (entity, prop, None)
            )
        )
        labels = filter(
            lambda label_tuple: filter_language(label_tuple[1]), labels
        )
        if not return_prop and not return_literal and not return_identifier:
            return (str(x[1]) for x in labels)
        elif return_prop and not return_literal and not return_identifier:
            return ((str(x[1]), x[0]) for x in labels)
        elif not return_prop and return_literal and not return_identifier:
            return (x[1] for x in labels)
        elif return_prop and return_literal and not return_identifier:
            return ((x[1], x[0]) for x in labels)
        elif not return_prop and not return_literal and return_identifier:
            return ((str(x[1]), x[2]) for x in labels)
        elif return_prop and not return_literal and return_identifier:
            return ((str(x[1]), x[0], x[2]) for x in labels)
        elif not return_prop and return_literal and return_identifier:
            return ((x[1], x[2]) for x in labels)
        else:  # everything true
            return ((x[1], x[0], x[2]) for x in labels)

    def get_identifiers(self) -> Set[Identifier]:
        """Get all the identifiers in the session."""
        return set(self.iter_identifiers())

    def get_entities(self) -> Set[OntologyEntity]:
        """Get all the entities stored in the session."""
        return {x for x in self}

    _interface_driver: Optional[InterfaceDriver] = None

    def _update_and_merge_helper(
        self,
        entity: OntologyEntity,
        mode: bool,
        visited: Optional[set] = None,
    ) -> None:
        """Private `merge` and `update` helper.

        Args:
            entity: The ontology entity to merge.
            mode: True means update, False means merge.
            visited: Entities that have already been updated or merged.
        """
        if entity.session is None:  # Newly created entity.
            if mode:
                self._graph.remove((entity.iri, None, None))
            for t in entity.graph.triples((None, None, None)):
                self._graph.add(t)
        elif entity not in self:  # Entity from another session.
            active_relationship = self.ontology.from_identifier(
                simphony_namespace.activeRelationship
            )
            try:
                existing = self.from_identifier(entity.identifier)
            except KeyError:
                existing = None

            self._track_identifiers(entity.identifier)

            # Clear old types, active relationships and attributes for
            # the update operation.
            if existing and mode:
                # Clear old types.
                self._graph.remove((existing.identifier, RDF.type, None))

                for p in existing.graph.predicates(existing.identifier, None):
                    try:
                        predicate = self.ontology.from_identifier(p)
                    except KeyError:
                        continue
                    # Clear attributes or active relationships.
                    if isinstance(predicate, OntologyAttribute) or (
                        isinstance(predicate, OntologyRelationship)
                        and active_relationship in predicate.superclasses
                    ):
                        self._graph.remove((existing.identifier, p, None))

            # Merge new types, active relationships and attributes.
            # The double for loop pattern (first loop over p, then loop over o)
            # is used because calling `self.ontology.from_identifier` is
            # expensive.
            visited = visited if visited is not None else set()
            for p in entity.graph.predicates(entity.identifier, None):
                try:
                    predicate = self.ontology.from_identifier(p)
                except KeyError:
                    # Merge new types.
                    if p == RDF.type:
                        for o in entity.graph.objects(entity.identifier, p):
                            self._graph.add((entity.identifier, p, o))
                    continue

                for o in entity.graph.objects(entity.identifier, p):
                    if isinstance(predicate, OntologyAttribute):
                        # Merge attributes.
                        self._graph.add((entity.identifier, p, o))
                    elif (
                        isinstance(predicate, OntologyRelationship)
                        and active_relationship in predicate.superclasses
                    ):
                        # Merge active relationships.
                        obj = entity.session.from_identifier(o)
                        if not isinstance(obj, OntologyIndividual):
                            continue
                        if obj.identifier not in visited:
                            visited.add(obj.identifier)
                            self._update_and_merge_helper(obj, mode, visited)
                        self._graph.add((entity.identifier, p, o))

    creation_set: Set[Identifier]
    _namespaces: Dict[URIRef, str]
    _graph: Graph
    _graph_writable: Graph
    _driver: Optional[Interface] = None

    @property
    def _session_linked(self) -> Session:
        return self

    def _track_identifiers(self, identifier, delete=False):
        # Keep track of new additions while inside context manager.
        if delete:
            self.creation_set.discard(identifier)
        else:
            entity_triples_exist = (
                next(self._graph.triples((identifier, None, None)), None)
                is not None
            )
            if not entity_triples_exist:
                self.creation_set.add(identifier)


class QueryResult(SPARQLResult):
    """SPARQL query result."""

    session: Session

    def __init__(self, *args, session: Optional[Session] = None, **kwargs):
        """Initialize the query result.

        Namely, a session is linked to this query result so that if ontology
        individuals are requested,

        Args:
            session: Session to which this result is linked to.
        """
        self.session = session or Session.get_default_session()
        super().__init__(*args, **kwargs)

    # ↓ --------------------- Public API --------------------- ↓ #

    def __call__(
        self, **kwargs
    ) -> Union[Iterator[Triple], Iterator[bool], Iterator[ResultRow]]:
        """Select the datatypes of the query results ofr SELECT queries.

        Args:
            **kwargs: For each variable name on the query, a callable
                can be specified as keyword argument. When retrieving
                results, this callable will be run on the RDFLib item from the
                result. Literals are an exception. The callable will
                be applied on top of the result of the `toPython()` method
                of the callable.

        Raises:
            ValueError: When the query that produced this result object is
                not a SELECT query.
        """
        if self.type != "SELECT":
            if kwargs:
                raise ValueError(
                    f"Result datatypes cannot be converted for "
                    f"{self.type} queries."
                )
            yield from self
            return

        for key, value in kwargs.items():
            """Filter certain provided callables and replace them by others."""
            if isclass(value) and issubclass(value, OntologyIndividual):
                """Replace OntologyIndividual with spawning the individual
                from its identifier."""
                kwargs[key] = lambda x: self.session.from_identifier_typed(
                    x, typing=OntologyIndividual
                )

        for row in self:
            """Yield the rows with the applied datatype transformation."""
            values = {
                Variable(var): kwargs.get(str(var), lambda x: x)(
                    row[i]
                    if not isinstance(row[i], Literal)
                    else row[i].toPython()
                )
                for i, var in enumerate(self.vars)
            }
            yield ResultRow(values, self.vars)

    # ↑ --------------------- Public API --------------------- ↑ #


Session.default_ontology = Session(
    identifier="default ontology", ontology=True
)
Session.set_default_session(Session(identifier="default session"))
# This default ontology is later overwritten by simphony_osp/utils/pico.py
