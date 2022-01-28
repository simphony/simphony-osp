"""Universal interface for wrapper developers."""

from abc import ABC, abstractmethod
from enum import IntEnum
from itertools import chain
from typing import Iterable, Iterator, Dict, Optional, Set, TYPE_CHECKING, \
    Tuple

from rdflib import Graph
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.query import Result
from rdflib.store import Store
from rdflib.term import Identifier, Node

from osp.core.interfaces.interface import Interface, Driver, BufferType
from osp.core.session import Session
from osp.core.utils.datatypes import Triple, UID, Pattern

if TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity

__all__ = ["OverlayInterface", "OverlayDriver"]


class OverlayDriver(Driver):
    """RDFLib store acting as intermediary between OSP-core and wrappers.

    Offers a triplestore interface for OSP-core to interact with wrappers.

     OSP-core <--> OverlayDriver <--> OverlayInterface

    The store is transaction aware (needs a commit action to save the changes
    to the wrapper). Otherwise, one would have to update an entity
    every time a single triple from the entity is added.
    """

    interface: 'OverlayInterface'
    session: Optional['Session'] = None

    @property
    def graph(self) -> Graph:
        return self.session.graph if self.session is not None else None

    _buffers: Dict[BufferType, Graph]
    _ontology: Optional['Session']

    # RDFLib
    # ↓ -- ↓

    context_aware = False
    formula_aware = False
    transaction_aware = True
    graph_aware = False

    def __init__(self,
                 *args,
                 interface: 'OverlayInterface',
                 ontology: Optional[Session] = None,
                 **kwargs):
        """Initialize the OverlayDriver.

        The initialization assigns an interface to the store and creates
        buffers for the store. Then the usual RDFLib's store initialization
        follows.
        """
        if not isinstance(interface, OverlayInterface):
            raise ValueError("No valid interface provided.")
        self.interface = interface
        self.interface.close()

        self._ontology = ontology
        self._reset_buffers()
        super().__init__(*args, interface=interface, **kwargs)

    def open(self, configuration: str, create: bool = False) -> None:
        """Asks the interface to open the data source."""
        self.interface.open(configuration, create)
        self.interface.session = Session(store=SimpleMemory(),
                                         ontology=self._ontology)
        self.interface.graph = self.interface.session.graph
        self.session = Session(store=self)
        try:
            self.interface.session.lock()
            with self.interface.session:
                self.interface.populate(
                    self.interface.graph,
                    self.interface.session)
        finally:
            self.interface.session.unlock()

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Tells the interface to close the data source.

        Args:
            commit_pending_transaction: commits uncommitted changes when
                true before closing the data source.
        """
        if commit_pending_transaction:
            self.commit()
        self.interface.close()
        self.session = None
        self.interface.session = None
        self.interface.graph = None

    def add(self, triple: Triple, context: Graph, quoted=False) -> None:
        """Adds triples to the store.

        Since the actual addition happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.DELETED]\
            .remove(triple)
        self._buffers[BufferType.ADDED]\
            .add(triple)

    def remove(self,
               triple_pattern: Pattern,
               context: Optional[Graph] = None) -> None:
        """Remove triples from the store.

        Since the actual removal happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.ADDED]\
            .remove(triple_pattern)
        existing_triples_to_delete = \
            self.interface.graph.triples(triple_pattern)
        for triple in existing_triples_to_delete:
            self._buffers[BufferType.DELETED]\
                .add(triple)

    def triples(self,
                triple_pattern: Pattern,
                context=None) -> Iterator[Tuple[Triple, Graph]]:
        """Query triples patterns.

        Merges the buffered changes with the data stored on the interface.
        """
        # Existing minus added and deleted triples.
        triple_pool = filter(
            lambda x: x not in chain(
                self._buffers[BufferType.DELETED].triples(triple_pattern),
                self._buffers[BufferType.ADDED].triples(triple_pattern)
            ),
            self.interface.graph.triples(triple_pattern)
        )
        # Include added triples (previously they were excluded in order not
        # to duplicate triples).
        triple_pool = chain(
            triple_pool,
            self._buffers[BufferType.ADDED].triples(triple_pattern))
        for triple in triple_pool:
            yield triple, iter(())

    def __len__(self, context: Graph = None) -> int:
        """Get the number of triples in the store.

        For more details, check RDFLib's documentation.
        """
        return sum(1 for _ in self.triples((None, None, None)))

    def bind(self, prefix, namespace):
        """Bind a namespace to a prefix."""
        raise NotImplementedError

    def namespace(self, prefix):
        """Get the namespace to which a prefix is bound."""
        raise NotImplementedError

    def prefix(self, namespace):
        """Get a bound namespace's prefix."""
        raise NotImplementedError

    def namespaces(self):
        """Get the bound namespaces."""
        raise NotImplementedError

    def query(self, *args, **kwargs) -> Result:
        """Perform a SPARQL query on the store."""
        return super().query(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Perform a SPARQL update query on the store."""
        return super().update(*args, **kwargs)

    def commit(self) -> None:
        """Commit buffered changes."""
        session, interface_session = self.session, self.interface.session

        # Find out from the triples which entities were added, updated and
        # deleted.
        class Tracker:
            """Checks whether entities already exist on the interface.

            In addition, it keeps track of entities for which existence has
            been already checked.
            """

            existing_subjects: set

            @property
            def visited_subjects(self) -> set:
                return (self.visited_subjects_minus_existing_subjects
                        | self.existing_subjects)

            _interface = self.interface

            def __init__(self):
                self.existing_subjects = set()
                self.visited_subjects_minus_existing_subjects = set()

            def __call__(self, subject: Node):
                if subject not in self.visited_subjects:
                    if next(self._interface.graph.triples(
                            (subject, None, None)), None) is not None:
                        self.existing_subjects.add(subject)
                    else:
                        self.visited_subjects_minus_existing_subjects.add(
                            subject)

        tracker = Tracker()

        # Get added subjects.
        for s in self._buffers[BufferType.ADDED].subjects():
            tracker(s)
        added_subjects = tracker.visited_subjects_minus_existing_subjects
        # Get deleted subjects.
        deleted_subjects = dict()
        for s in self._buffers[BufferType.DELETED].subjects():
            tracker(s)
            if (s not in added_subjects and s in
                    tracker.existing_subjects):
                deleted_subjects[s] = deleted_subjects.get(s, 0) + 1
        deleted_subjects = {
            s: True
            if count >= sum(1 for _ in self.interface.graph.triples(
                (s, None, None))) else False
            for s, count in deleted_subjects.items()
        }
        deleted_subjects = set(
            s for s, deleted in deleted_subjects.items() if deleted)
        # Get updated subjects.
        updated_subjects = tracker.existing_subjects.difference(
            deleted_subjects)
        added_entities = set(session.from_identifier(s) for s in
                             added_subjects)
        updated_entities = set(session.from_identifier(s)
                               for s in updated_subjects)
        deleted_entities = set(interface_session.from_identifier(s)
                               for s in deleted_subjects)

        # Calls commit on the interface.
        try:
            self.interface.session.lock()
            with self.interface.session:
                self.interface.commit(self.interface.graph, self.graph,
                                      self._buffers[BufferType.ADDED],
                                      self._buffers[BufferType.DELETED],
                                      self.interface.session, self.session,
                                      added_entities, updated_entities,
                                      deleted_entities)
        finally:
            self.interface.session.unlock()

        # Copy the triples from the buffers to the interface's graph.
        for t in self._buffers[BufferType.ADDED]:
            self.interface.graph.add(t)
        for t in self._buffers[BufferType.DELETED]:
            self.interface.graph.remove(t)

        # Clear the buffers.
        self._reset_buffers()

    def rollback(self) -> None:
        self._reset_buffers()

    # RDFLib
    # ↑ -- ↑

    def _reset_buffers(self) -> None:
        """Reset the contents of the buffers."""
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}


class OverlayInterface(ABC, Interface):
    """To be implemented by interface/wrapper developers."""

    # Definition of:
    # OverlayInterface
    # ↓ ------------ ↓

    @property
    @abstractmethod
    def root(self) -> Optional[Identifier]:
        """Define a custom root object.

        When desired, this property may return an IRI for a custom root
        entity for the wrapper. This is the IRI of the ontology entity that
        the user will get when invoking the wrapper. The method `populate`
        should have created such entity. Defining a custom root entity is
        OPTIONAL.

        When no IRI is provided by this property (`None` is returned),
        the user gets a virtual container instead. You cannot access such
        container.
        """
        return None

    @abstractmethod
    def open(self, configuration: str, create: bool = False):
        """Open the data source that the interface interacts with.

        You can expect calls to this method even when the data source is
        already open, therefore, an implementation like the following is
        recommended.

        def open(self, configuration: str, create: bool = False):
            if your_data_source_is_already_open:
                return
                # To improve the user experience you can check if the
                # configuration string leads to a resource different from
                # the current one and raise an error informing the user.

            # Connect to your data source...
            # your_data_source_is_already_open is for now True.

        Args:
            configuration: Determines the location of the data source to be
                opened.
            create: Whether the data source can be created at the target
                location if it does not exist. When false, if the data
                source does not exist, you should raise an exception. When
                true, create an empty data source.
        """
        pass

    @abstractmethod
    def close(self):
        """Close the data source that the interface interacts with.

        This method should NOT commit uncommitted changes.

        This method should close the connection that was obtained in `open`,
        and free any locked up resources.

        You can expect calls to this method even when the data source is
        already closed. Therefore, an implementation like the following is
        recommended.

        def close(self):
            if your_data_source_is_already_closed:
                return

            # Close the connection to your data source.
            # your_data_source_is_already_closed is for now True
        """
        pass

    @abstractmethod
    def commit(self,
               graph_old: Graph, graph_new: Graph,
               graph_diff_added: Graph, graph_diff_deleted: Graph,
               session_old: Session, session_new: Session,
               added: Set['OntologyEntity'], updated: Set['OntologyEntity'],
               deleted: Set['OntologyEntity']
               ):
        pass

    @abstractmethod
    def populate(self, graph: Graph, session: Session):
        pass

    # Definition of:
    # OverlayInterface
    # ↑ ------------ ↑

    session: Session
    graph: Graph
    driver: Store = OverlayDriver
