"""A user-facing class creating a session using a specific interface."""
import itertools
from abc import ABC, abstractmethod
from typing import Optional, Type, Union

from rdflib import RDF, Graph
from rdflib.graph import ReadOnlyGraphAggregate
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.query import Result
from rdflib.store import Store
from rdflib.term import Identifier

from simphony_osp.interfaces.interface import Interface, InterfaceDriver
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.interactive.container import Container
from simphony_osp.session.session import Session
from simphony_osp.utils.cuba_namespace import cuba_namespace
from simphony_osp.utils.datatypes import UID, Triple


class Wrapper:
    """A user-facing class for managing a session.

    The idea is to create hybrid subclasses from this class, for example
    ontology entities that are also able to manage sessions.

    Anything that has a `_session` attribute may be used to manage a session.
    """

    # Any class combined with the wrapper is expected to provide the two
    # properties below.
    session: Session
    interface: Optional[Interface] = None
    _session: Session
    _exit_container: bool = False

    def __enter__(self):
        """Enter the associated session's context."""
        self._session.__enter__()
        if isinstance(self, Container):
            Container.__enter__(self)
        return self

    def __exit__(self, *args):
        """Exit the associated session's context."""
        if isinstance(self, Container):
            self._exit_container = True
            Container.__exit__(self, *args)
            self._exit_container = False
        self._session.__exit__(*args)

    def commit(self) -> None:
        """Commit the changes made to the backend."""
        return self._session.commit()

    def close(self) -> None:
        """Close the connection to the backend."""
        if isinstance(self, Container):
            Container.close(self)
        if not self._exit_container:
            return self._session.close()

    def delete(self, *entities: OntologyEntity) -> None:
        """Delete entities from the backend."""
        for entity in entities:
            self._session.delete(entity)

    def compute(self, *args, **kwargs) -> None:
        """Instructs the backend to run a simulation if supported."""
        return self._session.compute(*args, **kwargs)


class WrapperSpawner(ABC, Wrapper):
    """A user-facing class for spawning a session."""

    @classmethod
    @abstractmethod
    def _get_interface(cls) -> Type[Interface]:
        """The type of interface that the instantiated session will use."""
        pass

    def __new__(
        cls,
        configuration_string: str = "",
        create: bool = False,
        *args,
        ontology: Optional[Union[Session, bool]] = None,
        root: Optional[Union[str, Identifier, "OntologyEntity"]] = None,
        **kwargs,
    ) -> Union["WrapperSpawner", OntologyEntity]:
        """Initialize the session using the wrapper's interface type.

        Creates an interface and a store using that interface. Then
        initialize the session using such store.
        """
        interface_class = cls._get_interface()

        # Initialize the session.
        interface_instance = interface_class(*args, **kwargs)
        store = InterfaceDriver(interface=interface_instance)
        graph = Graph(store=store)
        graph.open(configuration_string, create=create)
        session = Session(base=graph, driver=store, ontology=ontology)

        if all(x is not None for x in (root, interface_instance.root)):
            raise ValueError(
                "This Wrapper has a fixed root ontology "
                "entity, which can not be changed."
            )
        root = interface_instance.root or root

        # If not root has been defined, use a read-only container as root.
        if root is None:
            root = UID(0).to_identifier()
            container_store = VirtualContainerStore(session=session)
            graph = Graph(store=container_store, identifier=graph.identifier)
            session = Session(base=graph, driver=store, ontology=ontology)
            class_ = session.from_identifier(root).__class__
            uid = UID(root)
        else:
            if isinstance(root, OntologyEntity):
                session.update(root)
                class_ = root.__class__
                uid = UID(root.identifier)
            else:
                class_ = session.from_identifier(root).__class__
                uid = UID(root)
        class_ = type(
            f"Wrapping{class_.__name__}",
            (Wrapper, class_),
            {"interface": interface_instance},
        )
        entity = class_(uid=uid, session=session, merge=None)
        session._driver = store
        return entity

    @property
    def session(self) -> Session:
        """Returns the session that the wrapper is connected to."""
        return self._session


class VirtualContainerStore(Store):
    """RDFLib store that contains a virtual container object.

    Such container object is meant to be used as the wrapper.
    """

    store: Store
    session: Session

    # RDFLib
    # ↓ -- ↓

    formula_aware = False
    graph_aware = False
    context_aware = False

    @property
    def transaction_aware(self):
        """Whether the store is transaction-aware or not."""
        return self.store.transaction_aware

    def __init__(self, *args, session: Session, **kwargs):
        """Initialize the VirtualContainerStore."""
        self.store = session.graph.store
        self.session = session
        if any(
            getattr(self, attr) != getattr(self.store, attr)
            for attr in (
                "formula_aware",
                "graph_aware",
                "context_aware",
                "transaction_aware",
            )
        ):
            raise RuntimeError(
                f"The store must have the value"
                f"{self.formula_aware} for the property"
                f"`formula_aware` and the value "
                f"{self.graph_aware} for the property "
                f"`graph_aware`."
            )
        super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        """Asks the interface to open the data source."""
        return self.store.open(*args, **kwargs)

    def close(self, *args, **kwargs):
        """Tells the interface to close the data source."""
        return self.store.close(*args, **kwargs)

    def add(self, triple, context, quoted=False):
        """Adds triples to the store."""
        if not self._belongs_to_mock_container(triple):
            self.store.add(triple, context, quoted)
            return

        if triple[1] != cuba_namespace.contains:
            raise RuntimeError(
                "This container is read-only, except for the "
                "`cuba:Contains` relationship."
            )

    def remove(self, triple_pattern, context=None):
        """Remove triples from the store."""
        if not self._belongs_to_mock_container(triple_pattern):
            return self.store.remove(triple_pattern, context)
        if triple_pattern[1] == cuba_namespace.contains:
            if triple_pattern[2] is not None:
                self.session.delete(triple_pattern[2])
            else:
                for individual in set(
                    individual
                    for individual in self.session.get_entities()
                    if isinstance(individual, OntologyIndividual)
                ):
                    self.session.delete(individual)
        else:
            raise RuntimeError(
                "This container is read-only, except for the "
                "`cuba:Contains` relationship."
            )

    def triples(self, triple_pattern, context=None):
        """Query triples patterns.

        Merges the virtual container with the data stored on the store.
        """
        if not self._belongs_to_mock_container(triple_pattern):
            yield from self.store.triples(triple_pattern, context=None)
            return

        triples = iter(())
        # Type triple.
        if triple_pattern[1] in (RDF.type, None) and triple_pattern[2] in (
            cuba_namespace.Container,
            None,
        ):
            triples = itertools.chain(
                triples,
                (
                    (
                        UID(0).to_identifier(),
                        RDF.type,
                        cuba_namespace.Container,
                    ),
                ),
            )

        # Entities contained.
        if triple_pattern[1] in (cuba_namespace.contains, None):
            if triple_pattern[2] is None:
                triples = itertools.chain(
                    triples,
                    (
                        (
                            UID(0).to_identifier(),
                            cuba_namespace.contains,
                            individual.identifier,
                        )
                        for individual in self.session.get_entities()
                        if isinstance(individual, OntologyIndividual)
                    ),
                )
            else:
                try:
                    self.session.from_identifier(triple_pattern[2])
                    triples = itertools.chain(
                        triples,
                        (
                            (
                                UID(0).to_identifier(),
                                cuba_namespace.contains,
                                triple_pattern[2],
                            ),
                        ),
                    )
                except KeyError:
                    pass

        yield from (((t[0], t[1], t[2]), iter(())) for t in triples)
        for x in self.store.triples(triple_pattern, context=None):
            yield x
        # yield from self.store.triples(triple_pattern, context=None)

    def __len__(self, *args, **kwargs):
        """Get the number of triples in the store."""
        return sum(
            1 for _ in self.triples((UID(0).to_identifier(), None, None))
        ) + self.store.__len__(*args, **kwargs)

    def bind(self, *args, **kwargs):
        """Bind a namespace to a prefix."""
        return self.store.bind(*args, **kwargs)

    def namespace(self, *args, **kwargs):
        """Bind a namespace to a prefix."""
        return self.store.namespace(*args, **kwargs)

    def prefix(self, *args, **kwargs):
        """Get a bound namespace's prefix."""
        return self.store.prefix(*args, **kwargs)

    def namespaces(self):
        """Get the bound namespaces."""
        return self.store.namespaces()

    def query(
        self, query, init_ns, init_bindings, query_graph, **kwargs
    ) -> Result:
        """Perform a SPARQL query on the store."""
        # TODO: better algorithm.
        g1, g2 = Graph(store=SimpleMemory()), Graph(store=self.store)
        for t, _ in self.triples((UID(0).to_identifier(), None, None)):
            g1.add(t)
        ro = ReadOnlyGraphAggregate([g1, g2])
        return ro.query(
            query, initNs=init_ns, initBindings=init_bindings, **kwargs
        )

    def update(self, *args, **kwargs):
        """Perform a SPARQL update query on the store."""
        raise NotImplementedError
        # return self.store.update(*args, **kwargs)

    def commit(self):
        """Commit buffered changes."""
        return self.store.commit()

    def rollback(self):
        """Discard uncommitted changes."""
        return self.store.rollback()

    # RDFLib
    # ↑ -- ↑

    @staticmethod
    def _belongs_to_mock_container(triple: Triple) -> bool:
        pattern = (UID(0).to_identifier(), None, None)
        mask = tuple(
            triple[i] == pattern[i] if pattern[i] is not None else True
            for i in range(0, 3)
        )
        return all(mask)
