"""Abstract Base Class for all Sessions."""
from __future__ import annotations

import itertools
import logging
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
from rdflib.graph import ReadOnlyGraphAggregate
from rdflib.plugins.sparql.processor import SPARQLResult
from rdflib.query import ResultRow
from rdflib.term import Identifier, Node, Variable

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.ontology.utils import compatible_classes
from simphony_osp.utils import simphony_namespace
from simphony_osp.utils.datatypes import UID, Triple

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simphony_osp.interfaces.interface import Interface, InterfaceDriver

ENTITY = TypeVar("ENTITY", bound=OntologyEntity)


class Environment:
    """Environment where ontology entities may be created.

    E.g. sessions, containers.
    """

    # ↓ --------------------- Public API --------------------- ↓ #

    def lock(self):
        """Increase the lock count.

        See the docstring of `locked` for an explanation of what locking an
        environment means.
        """
        self._lock += 1

    def unlock(self):
        """Decrease the lock count.

        See the docstring of `locked` for an explanation of what locking an
        environment means.
        """
        self._lock = self._lock - 1 if self._lock > 0 else 0

    @property
    def locked(self) -> bool:
        """Whether the environment is locked or not.

        A locked environment will not be closed when using it as a context
        manager and leaving the context. Useful for setting it as the
        default environment when it is not intended to close it afterwards.
        """
        return self._lock > 0

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


class Session(Environment):
    """Interface to a Graph containing OWL ontology entities."""

    # ↓ --------------------- Public API --------------------- ↓ #
    """These methods are meant to be available to the end-user."""

    identifier: Optional[str] = None
    """A label for the session.

    The identifier is just a label for the session to be displayed within
    Python (string representation of the session). It has no other effect.
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
        self._ontology = value

    label_properties: Tuple[URIRef] = (SKOS.prefLabel, RDFS.label)
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
    `label_properties` docstring above, this list will also be checked from
    left to right. When one of the languages specified is available,
    this will define the default label. Then the default label will default to
    english. If also not available, then any language will be used.
    """

    def commit(self) -> None:
        """Commit pending changes to the session's graph."""
        self._graph.commit()
        if self.ontology is not self:
            self.ontology.commit()
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

        The query is performed on the session's data (the ontology is not
        included).

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

    def __contains__(self, item: OntologyEntity):
        """Check whether an ontology entity is stored on the session."""
        return item.session is self

    def __iter__(self) -> Iterator[OntologyEntity]:
        """Iterate over all the ontology entities in the session.

        This operation can be computationally VERY expensive.
        """
        # Warning: entities can be repeated.
        return (
            self.from_identifier(identifier)
            for identifier in self.iter_identifiers()
        )

    def __len__(self) -> int:
        """Return the number of ontology entities within the session."""
        return sum(1 for _ in self)

    def __str__(self):
        """Convert the session to a string."""
        # TODO: Return the kind of RDFLib store attached too.
        return (
            f"<{self.__class__.__module__}.{self.__class__.__name__}: "
            f"{self.identifier if self.identifier is not None else ''} "
            f"at {hex(id(self))}>"
        )

    @lru_cache(maxsize=4096)
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

        """Look for compatible Python classes to spawn."""
        compatible = set()

        for rdf_type in self._graph.objects(identifier, RDF.type):
            # Look for compatible embedded classes.
            found = compatible_classes(rdf_type, identifier)
            if not found:
                # If not an embedded class, then the type may be known in
                # the ontology. This means that an ontology individual would
                # have to be spawned.
                try:
                    self.ontology.from_identifier(rdf_type)
                    compatible |= {OntologyIndividual}
                except KeyError:
                    pass
            else:
                compatible |= found

        """Some ontologies are hybrid RDFS and OWL ontologies (i.e. FOAF).
        In such cases, object and datatype properties are preferred to
        annotation properties."""
        if OntologyAnnotation in compatible and any(
            x in compatible for x in (OntologyRelationship, OntologyAttribute)
        ):
            compatible.remove(OntologyAnnotation)
        if len(compatible) == 0:
            # The individual belongs to an unknown class.
            raise KeyError(
                f"Identifier {identifier} does not match any OWL "
                f"entity, any entity natively supported by "
                f"SimPhoNy, nor an ontology individual "
                f"belonging to a class in the ontology."
            )
        elif len(compatible) >= 2:
            compatible = map(str, compatible)
            raise RuntimeError(
                f"Two or more python classes ("
                f"{', '.join(compatible)}) "
                f"could be spawned from {identifier}."
            )
        else:
            python_class = compatible.pop()
            return python_class(uid=UID(identifier), session=self, merge=None)

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

    @lru_cache(maxsize=4096)
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
    ) -> Union[OntologyIndividual, FrozenSet[OntologyIndividual]]:
        """Copies the ontology entities to the session."""
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
        delete = (
            (individual.identifier, None, None)
            for individual in individuals
            if individual.session is not self
        )
        add = (
            (s, p, o)
            for individual in individuals
            for s, p, o in individual.session.graph.triples(
                (individual.identifier, None, None)
            )
            if (p == RDF.type or isinstance(o, Literal) or o in identifiers)
        )
        if not merge:
            """Replace previous individuals if merge is False."""
            for pattern in delete:
                self.graph.remove(pattern)
        self.graph.addN((s, p, o, self.graph) for s, p, o in add)
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
        """Remove an ontology entity from the session."""
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

    def clear(self):
        """Clear all the data stored in the session."""
        self._graph.remove((None, None, None))
        self._namespaces.clear()
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

    # ↑ --------------------- Public API --------------------- ↑ #

    default_ontology: Session
    """The default ontology.

    When no T-Box is explicitly assigned to a session, this is the ontology
    it makes use of.
    """

    _ontology: Optional[Session] = None

    def __init__(
        self,
        base: Optional[Graph] = None,  # The graph must be OPEN already.
        driver: Optional[InterfaceDriver] = None,
        ontology: Optional[Union[Session, bool]] = None,
        identifier: Optional[str] = None,
        namespaces: Dict[str, URIRef] = None,
        from_parser: Optional[OntologyParser] = None,
    ):
        """Initialize the session."""
        super().__init__()
        self._environment_references.add(self)
        # Base the session graph either on a store if passed or an empty graph.
        if base is not None:
            self._graph = base
        else:
            self._graph = Graph()

        self._interface_driver = driver

        # Configure the ontology for this session
        if isinstance(ontology, Session):
            self.ontology = ontology
        elif ontology is True:
            self.ontology = self
        elif ontology is not None:
            raise TypeError(
                f"Invalid ontology argument: {ontology}."
                f"Expected either a `Session` or `bool` object, "
                f"got {type(ontology)} instead."
            )

        # Bypass cache if this session is not a T-Box
        if self.ontology is not self:

            def bypass_cache(method: Callable):
                wrapped_func = method.__wrapped__

                @wraps(wrapped_func)
                def bypassed(*args, **kwargs):
                    return wrapped_func(self, *args, **kwargs)

                bypassed.cache_clear = lambda: None
                return bypassed

            self.from_identifier = bypass_cache(self.from_identifier)
            self.from_label = bypass_cache(self.from_label)

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
            self.ontology._graph.bind(name, iri)

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
        self.ontology._graph += parser.graph
        for name, iri in parser.namespaces.items():
            self.bind(name, iri)
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

        # Yield the entities from the TBox (literals filtered out above).
        if self.ontology is self:
            yield from (
                s
                for t in supported_entity_types
                for s in self.ontology.graph.subjects(RDF.type, t)
                if not isinstance(s, Literal)
            )

        # Yield the entities from the ABox (literals filtered out below).
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

        labels = filter(
            lambda label_tuple: filter_language(label_tuple[1]),
            (
                (prop, literal, subject)
                for prop in self.label_properties
                for subject, _, literal in self._graph.triples(
                    (entity, prop, None)
                )
            ),
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
        return set(x for x in self)

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
