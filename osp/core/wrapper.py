"""A user-facing class creating a session using a specific interface."""
import itertools
from abc import ABC, abstractmethod
from typing import Optional, Type, Union

from rdflib import Graph
from rdflib import RDF
from rdflib.graph import ReadOnlyGraphAggregate
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.store import Store

from rdflib.term import Identifier

from osp.core.session import Session
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.individual import OntologyIndividual
# from osp.core.ontology.interactive.container import Container
from osp.core.interfaces.interface import Interface
from osp.core.utils.cuba_namespace import cuba_namespace
from osp.core.utils.datatypes import UID, Triple


class Wrapper:
    """A user-facing class for managing a session.

    The idea is to create hybrid subclasses from this class, for example
    ontology entities that are also able to manage sessions.

    Anything that has a `_session` attribute may be used to manage a session.
    """

    # Any class combined with the wrapper is expected to provide the two
    # properties below.
    session: Session
    _session: Session

    def __enter__(self):
        """Enter the associated session's context."""
        self._session.__enter__()
        # if isinstance(self, Container):
        #     Container.__enter__(self)
        return self

    def __exit__(self, *args):
        """Exit the associated session's context."""
        # if isinstance(self, Container):
        #     Container.__exit__(self, *args)
        self._session.__exit__(*args)

    def commit(self) -> None:
        """Commit the changes made to the backend."""
        return self._session.commit()

    def close(self) -> None:
        """Close the connection to the backend."""
        return self._session.close()

    def run(self) -> None:
        """Instructs the backend to run a simulation if supported."""
        return self._session.run()


class WrapperSpawner(ABC, Wrapper):
    """A user-facing class for spawning a session."""

    @classmethod
    @abstractmethod
    def _get_interface(cls) -> Type[Interface]:
        """The type of interface that the instantiated session will use."""
        pass

    def __new__(cls,
                configuration_string: str = '',
                *args,
                ontology: Optional[Union[Session, bool]] = None,
                root: Optional[Union[str,
                                     Identifier,
                                     'OntologyEntity']] = None,
                **kwargs) -> Union['WrapperSpawner', OntologyEntity]:
        """Initialize the session using the wrapper's interface type.

        Creates an interface and a store using that interface. Then
        initialize the session using such store.
        """
        interface_class = cls._get_interface()
        if all(x is not None for x in (root, interface_class.root)):
            raise ValueError("This Wrapper has a fixed root ontology "
                             "entity, which can not be changed.")
        root = interface_class.root or root

        # Initialize the session.
        interface_instance = interface_class(configuration_string,
                                             *args,
                                             **kwargs)
        store = cls._get_interface().store_class(interface=interface_instance)
        store.open(configuration_string)
        session = Session(store=store, ontology=ontology)

        # If not root has been defined, use a read-only container as root.
        if root is None:
            root = UID(0).to_identifier()
            container_store = MockContainerStore(session=session)
            session = Session(store=container_store,
                              ontology=ontology)
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
        class_ = type(f"Wrapping{class_.__name__}",
                      (Wrapper, class_), {})
        entity = class_(uid=uid, session=session, merge=None)
        return entity

    @property
    def session(self) -> Session:
        """Returns the session that the wrapper is connected to."""
        return self._session


class MockContainerStore(Store):
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

    def __init__(self,
                 *args,
                 session: Session,
                 **kwargs):
        """Initialize the MockContainerStore."""
        self.store = session.graph.store
        self.session = session
        if any(getattr(self, attr) != getattr(self.store, attr)
               for attr in ('formula_aware', 'graph_aware',
                            'context_aware', 'transaction_aware')):
            raise RuntimeError(f"The store must have the value"
                               f"{self.formula_aware} for the property"
                               f"`formula_aware` and the value "
                               f"{self.graph_aware} for the property "
                               f"`graph_aware`.")
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
            raise RuntimeError("This container is read-only, except for the "
                               "`cuba:Contains` relationship.")

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
                        if isinstance(individual, OntologyIndividual)):
                    self.session.delete(individual)
        else:
            raise RuntimeError("This container is read-only, except for the "
                               "`cuba:Contains` relationship.")

    def triples(self, triple_pattern, context=None):
        """Query triples patterns.

        Merges the virtual container with the data stored on the store.
        """
        if not self._belongs_to_mock_container(triple_pattern):
            yield from self.store.triples(triple_pattern, context=None)
            return

        triples = iter(())
        # Type triple.
        if (triple_pattern[1] in (RDF.type, None)
                and triple_pattern[2] in (cuba_namespace.Container, None)):
            triples = itertools.chain(
                triples,
                ((UID(0).to_identifier(),
                  RDF.type,
                  cuba_namespace.Container),
                 ), )

        # Entities contained.
        if triple_pattern[1] in (cuba_namespace.contains, None):
            if triple_pattern[2] is None:
                triples = itertools.chain(
                    triples,
                    ((UID(0).to_identifier(),
                     cuba_namespace.contains,
                     individual.identifier)
                     for individual in self.session.get_entities()
                     if isinstance(individual, OntologyIndividual))
                )
            else:
                try:
                    self.session.from_identifier(triple_pattern[2])
                    triples = itertools.chain(
                        triples,
                        ((UID(0).to_identifier(),
                          cuba_namespace.contains,
                          triple_pattern[2]), )
                    )
                except KeyError:
                    pass

        result = itertools.chain(
            triples,
            self.store.triples(triple_pattern, context=None)
        )
        for triple in result:
            yield triple, iter(())

    def __len__(self, *args, **kwargs):
        """Get the number of triples in the store."""
        return (
            sum(1 for _ in self.triples((UID(0).to_identifier(), None, None)))
            + self.store.__len__(*args, **kwargs))

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

    def query(self, *args, **kwargs):
        """Perform a SPARQL query on the store."""
        g1, g2 = Graph(store=SimpleMemory()), Graph(store=self.store)
        for t in self.triples((UID(0).to_identifier(), None, None)):
            g1.add(t)
        ro = ReadOnlyGraphAggregate([g1, g2])
        return ro.query(*args, **kwargs)

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
        mask = tuple(triple[i] == pattern[i]
                     if pattern[i] is not None else True
                     for i in range(0, 3))
        return all(mask)
