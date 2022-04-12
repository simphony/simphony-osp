"""Universal interface for wrapper developers."""

from abc import ABC, abstractmethod
from enum import IntEnum
from itertools import chain
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    Dict,
    Iterator,
    Optional,
    Set,
    Tuple,
)

from rdflib import RDF, Graph, URIRef
from rdflib.graph import ModificationException, ReadOnlyGraphAggregate
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.query import Result
from rdflib.store import Store
from rdflib.term import Identifier, Node

from simphony_osp.session.session import Session
from simphony_osp.utils.cuba_namespace import cuba_namespace
from simphony_osp.utils.datatypes import Pattern, Triple

if TYPE_CHECKING:
    from simphony_osp.ontology.entity import OntologyEntity

__all__ = [
    "BufferType",
    "BufferedSimpleMemoryStore",
    "Interface",
    "InterfaceDriver",
]


class BufferType(IntEnum):
    """Enum representing the two possible types of triple buffers.

    - ADDED: For triples that have been added.
    - DELETED: For triples that have been deleted.
    """

    ADDED = 0
    DELETED = 1


class BufferedSimpleMemoryStore(SimpleMemory):
    """A transaction-aware extension of the RDFLib SimpleMemory store."""

    _buffers: Dict[BufferType, Graph]
    """Holds added and removed triples until a commit is performed."""

    # RDFLib
    # ↓ -- ↓

    transaction_aware = True

    def __init__(self, *args, **kwargs):
        """Initialize the store."""
        self._reset_buffers()  # Creates the buffers for the first time.
        super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs) -> Optional[int]:
        """Opens the store.

        Resets the buffers before performing the operation.
        """
        self._reset_buffers()
        return super().open(*args, **kwargs)

    def close(self, *args, **kwargs) -> None:
        """Closes the store.

        Resets the buffers after having closed the `SimpleMemory` store.
        """
        result = super().close(*args, **kwargs)
        self._reset_buffers()
        return result

    def add(self, triple: Triple, context: Graph, quoted=False) -> None:
        """Add triples to the store.

        Since this store is meant to be transaction-aware, the changes are
        just buffered until a commit is performed.
        """
        self._buffers[BufferType.DELETED].remove(triple)
        self._buffers[BufferType.ADDED].remove(triple)

    def remove(
        self, triple_pattern: Pattern, context: Optional[Graph] = None
    ) -> None:
        """Remove triples from the store.

        Since this store is transaction-aware, the changes are buffered
        until a commit is performed.
        """
        self._buffers[BufferType.ADDED].remove(triple_pattern)
        existing_triples = (
            (s, p, o) for (s, p, o), ctx in self.triples(triple_pattern)
        )
        for triple in existing_triples:
            self._buffers[BufferType.DELETED].add(triple)

    def triples(
        self, triple_pattern: Pattern, context=None, ignore_buffers=False
    ) -> Iterator[Tuple[Triple, Iterator[Graph]]]:
        """Fetch triples from the store that match the given pattern.

        The triples from the underlying `SimpleMemory` store are combined
        with the contents of the buffers to produce the final result
        """
        triple_pool = filter(
            lambda x: x
            not in chain(
                self._buffers[BufferType.ADDED].triples(triple_pattern),
                self._buffers[BufferType.DELETED].triples(triple_pattern),
            ),
            (
                (s, p, o)
                for (s, p, o), ctx in super().triples(triple_pattern, None)
            ),
        )
        # Include added triples (previously they were excluded in order not
        # to duplicate triples).
        triple_pool = chain(
            triple_pool,
            self._buffers[BufferType.ADDED].triples(triple_pattern),
        )

        yield from ((triple, iter(())) for triple in triple_pool)

    def query(self, *args, **kwargs) -> Result:
        """Perform a SPARQL query on the store."""
        # TODO: use the store's implementation when the buffers are empty.
        raise NotImplementedError  # Just use RDFLib's query processor.

    def update(self, *args, **kwargs) -> None:
        """Perform s SPARQL update query on the store."""
        # TODO: use the store's implementation when the buffers are empty.
        raise NotImplementedError  # Just use RDFLib's query processor.

    def commit(self) -> None:
        """Commit buffered changes to the underlying `SimpleMemory` store."""
        # Remove triples from deleted buffer.
        for triple in self._buffers[BufferType.DELETED]:
            super().remove(triple, None)

        # Add triples from added buffer.
        super().addN(
            (s, p, o, None) for s, p, o in self._buffers[BufferType.ADDED]
        )

        self._reset_buffers()

        super().commit()

    def rollback(self) -> None:
        """Revert buffered changes."""
        self._reset_buffers()
        super().rollback()

    # RDFLib
    # ↑ -- ↑

    def _reset_buffers(self) -> None:
        """Replaces the existing buffers by empty buffers."""
        self._buffers = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }


class InterfaceDriver(Store):
    """RDFLib store acting as intermediary between SimPhoNy and wrappers.

    Offers a triplestore interface for SimPhoNy to interact with wrappers.

     SimPhoNy <--> InterfaceDriver <--> Interface

    The store is transaction aware (needs a commit action to save the changes
    to the wrapper). Otherwise, one would have to update an entity
    every time a single triple from the entity is added.
    """

    interface: "Interface"
    """The interface that the driver controls."""

    _buffer_caught: Dict[BufferType, Graph]
    """Holds triples that should not be added to the interface's base graph."""

    _buffer_uncaught: Dict[BufferType, Graph]
    """Holds triples that should be added to the interface's base graph."""

    _queue: Dict[URIRef, Optional[BinaryIO]]
    """Holds handles of files to be uploaded, URIs of files to be deleted."""

    _ontology: Optional["Session"]
    """Ontology to be used on the session's shown to the wrapper developer."""

    # RDFLib
    # ↓ -- ↓

    context_aware: bool = False
    formula_aware: bool = False
    transaction_aware: bool = True
    graph_aware: bool = False

    def __init__(
        self,
        *args,
        interface: "Interface",
        ontology: Optional[Session] = None,
        **kwargs
    ):
        """Initialize the InterfaceDriver.

        The initialization assigns an interface to the store and creates
        buffers. Then the usual RDFLib's store initialization follows.
        """
        if not isinstance(interface, Interface):
            raise ValueError("No valid interface provided.")

        interface.close()
        self.interface = interface

        self._buffer_uncaught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
        self._buffer_caught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }

        self._ontology = ontology
        self._queue = dict()
        super().__init__(*args, **kwargs)

    def open(self, configuration: str, create: bool = False) -> None:
        """Asks the interface to open the data source."""
        # Reset buffers
        self._buffer_uncaught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
        self._buffer_caught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }

        self.interface.open(configuration, create)

        # The interface can set its base graph when `open` is called. If not
        # set by the interface, then an in-memory transaction-aware graph is
        # used. A session based on this graph is also provided to the
        # interface.
        if self.interface.base is None:
            self.interface.base = Graph(store=BufferedSimpleMemoryStore())
        self.interface.session_base = Session(
            base=self.interface.base, ontology=self._ontology
        )

        # Call the populate method of the interface on base graph/session.
        # The populate method is meant to act on the base graph.
        session = self.interface.session_base
        try:
            session.lock()
            # Session must not close when exiting its context manager (just
            # in case the user enters the context manager again inside
            # populate).
            with session:
                self.interface.populate()
        finally:
            session.unlock()

        self.interface.session_base = None

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Tells the interface to close the data source.

        Args:
            commit_pending_transaction: commits uncommitted changes when
                true before closing the data source.
        """
        if commit_pending_transaction:
            self.commit()
        self.interface.close()
        # Clear all sessions, graphs, and entities provided to the interface.
        self.interface.base = None
        self.interface.old_graph = None
        self.interface.new_graph = None
        self.interface.buffer = None
        self.interface.session_base = None
        self.interface.session_old = None
        self.interface.session_new = None
        self.interface.added = None
        self.interface.updated = None
        self.interface.deleted = None

    def add(self, triple: Triple, context: Graph, quoted=False) -> None:
        """Adds triples to the interface.

        Since the actual addition happens during a commit, this method just
        buffers the changes.
        """
        buffer = (
            self._buffer_caught
            if hasattr(self.interface, "add")
            and not self.interface.add(triple)
            else self._buffer_uncaught
        )

        buffer[BufferType.DELETED].remove(triple)
        buffer[BufferType.ADDED].add(triple)

    def remove(
        self, triple_pattern: Pattern, context: Optional[Graph] = None
    ) -> None:
        """Remove triples from the interface.

        Since the actual removal happens during a commit, this method just
        buffers the changes.
        """
        for buffer in (self._buffer_uncaught, self._buffer_caught):
            buffer[BufferType.ADDED].remove(triple_pattern)
            existing_triples = (
                self.interface.base.triples(triple_pattern)
                if buffer is self._buffer_uncaught
                else (
                    set(self.interface.remove(triple_pattern))
                    if hasattr(self.interface, "remove")
                    else set()
                )
            )
            for triple in existing_triples:
                buffer[BufferType.DELETED].add(triple)

    def triples(
        self, triple_pattern: Pattern, context=None, ignore_buffers=False
    ) -> Iterator[Tuple[Triple, Graph]]:
        """Query the interface for triple patterns.

        This method combines the information on the buffers with the one
        provided by the interface. Moreover, if defined, it will use the
        `triples` method of the interface so that it can watch which triples
        are being retrieved or produce triples from its data structures on
        the fly.
        """
        # Existing minus added and deleted triples.
        if hasattr(self.interface, "triples"):
            query_method = self.interface.triples
        else:
            query_method = self.interface.base.triples

        triple_pool = query_method(triple_pattern)
        if not ignore_buffers:
            triple_pool = filter(
                lambda x: x
                not in chain(
                    self._buffer_uncaught[BufferType.DELETED].triples(
                        triple_pattern
                    ),
                    self._buffer_caught[BufferType.DELETED].triples(
                        triple_pattern
                    ),
                    self._buffer_uncaught[BufferType.ADDED].triples(
                        triple_pattern
                    ),
                    self._buffer_caught[BufferType.ADDED].triples(
                        triple_pattern
                    ),
                ),
                triple_pool,
            )
            # Include added triples (previously they were excluded in order not
            # to duplicate triples).
            triple_pool = chain(
                triple_pool,
                self._buffer_uncaught[BufferType.ADDED].triples(
                    triple_pattern
                ),
                self._buffer_caught[BufferType.ADDED].triples(triple_pattern),
            )

        yield from ((triple, iter(())) for triple in triple_pool)

    def __len__(self, context: Graph = None, ignore_buffers=False) -> int:
        """Get the number of triples in the store."""
        # TODO: faster algorithm.
        return sum(
            1 for _ in self.triples((None, None, None), ignore_buffers=True)
        )

    def bind(self, prefix, namespace):
        """Bind a namespace to a prefix."""
        return super().bind(prefix, namespace)

    def namespace(self, prefix):
        """Get the namespace to which a prefix is bound."""
        return super().namespace(prefix)

    def prefix(self, namespace):
        """Get a bound namespace's prefix."""
        return super().prefix(namespace)

    def namespaces(self):
        """Get the bound namespaces."""
        return super().namespaces()

    def query(
        self, query, init_ns, init_bindings, query_graph, **kwargs
    ) -> Result:
        """Perform a SPARQL query on the store."""
        if (
            sum(
                len(x)
                for x in (
                    buffer[y]
                    for buffer in (self._buffer_uncaught, self._buffer_caught)
                    for y in (BufferType.ADDED, BufferType.DELETED)
                )
            )
            > 0
        ):
            # TODO: raise warning that committing can increase query
            #  performance.
            raise NotImplementedError
        elif hasattr(self.interface, "triples"):
            if hasattr(self.interface, "query"):
                # TODO: translate init_ns and init_bindings.
                return self.interface.query(query)
            else:
                raise NotImplementedError
        else:
            return self.interface.base.query(
                query, initNs=init_ns, initBindings=init_bindings, **kwargs
            )

    def update(self, query, init_ns, init_bindings, query_graph, **kwargs):
        """Perform a SPARQL update query on the store."""
        if (
            sum(
                len(x)
                for x in (
                    buffer[y]
                    for buffer in (self._buffer_uncaught, self._buffer_caught)
                    for y in (BufferType.ADDED, BufferType.DELETED)
                )
            )
            > 0
        ):
            # TODO: raise warning that committing can increase query
            #  performance.
            raise NotImplementedError
        elif hasattr(self.interface, "triples"):
            if hasattr(self.interface, "update"):
                return self.interface.update(query)
            else:
                raise NotImplementedError
        else:
            return self.interface.base.update(
                query, initNs=init_ns, initBindings=init_bindings, **kwargs
            )

    def commit(self) -> None:
        """Commit buffered changes."""
        # Gets the old and new graphs and let the interface access a
        # read-only version of them.
        self.interface.old_graph = Graph(
            store=InterfaceDriver.UnbufferedInterfaceDriver(driver=self)
        )
        self.interface.new_graph = ReadOnlyGraphAggregate([Graph(store=self)])

        # Lets the interface access the buffer of caught triples.
        self.interface.buffer = self._buffer_caught

        # Creates the base, old and new sessions for the interface.
        self.interface.session_base = Session(
            base=self.interface.base, ontology=self._ontology
        )
        self.interface.session_old = Session(
            base=self.interface.old_graph, ontology=self._ontology
        )
        self.interface.session_new = Session(
            base=self.interface.new_graph, ontology=self._ontology
        )

        # Computes updated, added and deleted entities if enabled.
        if not self.interface.disable_entity_tracking:
            (
                added_entities,
                updated_entities,
                deleted_entities,
            ) = self._compute_entity_modifications()
            self.interface.added = added_entities
            self.interface.updated = updated_entities
            self.interface.deleted = deleted_entities

        # Calls commit on the interface.
        session = self.interface.session_new
        try:
            session.lock()
            with session:
                self.interface.commit()
        finally:
            session.unlock()

        # Copies the uncaught triples from the buffers to the base graph.
        for triple in self._buffer_uncaught[BufferType.DELETED]:
            self.interface.base.remove(triple)
        self.interface.base.addN(
            (s, p, o, self.interface.base)
            for s, p, o in self._buffer_uncaught[BufferType.ADDED]
        )
        self.interface.base.commit()

        # Queue file removal for removed file objects.
        for s in chain(
            self._buffer_uncaught[BufferType.DELETED][
                : RDF.type : cuba_namespace.File
            ],
            self._buffer_caught[BufferType.DELETED][
                : RDF.type : cuba_namespace.File
            ],
        ):
            self.queue(s, None)
        for URI, file in self._queue.items():
            if file is None:
                self.interface.delete(URI)
            else:
                self.interface.save(URI, file)
                file.close()

        # Reset buffers and file queue.
        self._buffer_uncaught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
        self._buffer_caught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
        self._queue = dict()

        # Reset graphs, sessions and entities passed to the interface.
        self.interface.old_graph = None
        self.interface.new_graph = None
        self.interface.buffer = None
        self.interface.session_base = None
        self.interface.session_old = None
        self.interface.session_new = None
        self.interface.added = None
        self.interface.updated = None
        self.interface.deleted = None

    def rollback(self) -> None:
        """Discard uncommitted changes."""
        self._buffer_uncaught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
        self._buffer_caught = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
        for file in self._queue.values():
            if file is not None:
                file.close()
        self._queue = dict()

    # RDFLib
    # ↑ -- ↑

    def compute(self, *args, **kwargs):
        """Compute new information (e.g. run a simulation)."""
        if not hasattr(self.interface, "compute"):
            return None

        self.interface.session_base = Session(
            base=self.interface.base, ontology=self._ontology
        )
        session = self.interface.session_base
        try:
            session.lock()
            with session:
                self.interface.compute(*args, **kwargs)
        finally:
            session.unlock()
        self.interface.session_base = None

    def queue(self, key: URIRef, file: Optional[BinaryIO]) -> None:
        """Queue a file to be committed."""
        self._queue[key] = file

    def _compute_entity_modifications(
        self,
    ) -> Tuple[
        Set["OntologyEntity"], Set["OntologyEntity"], Set["OntologyEntity"]
    ]:

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
                return (
                    self.visited_subjects_minus_existing_subjects
                    | self.existing_subjects
                )

            _interface = self.interface

            def __init__(self):
                self.existing_subjects = set()
                self.visited_subjects_minus_existing_subjects = set()

            def __call__(self, subject: Node):
                if subject not in self.visited_subjects:
                    if (
                        next(
                            self._interface.old_graph.triples(
                                (subject, None, None)
                            ),
                            None,
                        )
                        is not None
                    ):
                        self.existing_subjects.add(subject)
                    else:
                        self.visited_subjects_minus_existing_subjects.add(
                            subject
                        )

        tracker = Tracker()

        # Get added subjects.
        for s in chain(
            self._buffer_uncaught[BufferType.ADDED].subjects(),
            self._buffer_caught[BufferType.ADDED].subjects(),
        ):
            tracker(s)
        added_subjects = tracker.visited_subjects_minus_existing_subjects
        # Get deleted subjects.
        deleted_subjects = dict()
        for s in chain(
            self._buffer_uncaught[BufferType.DELETED].subjects(),
            self._buffer_caught[BufferType.DELETED].subjects(),
        ):
            tracker(s)
            if s not in added_subjects and s in tracker.existing_subjects:
                deleted_subjects[s] = deleted_subjects.get(s, 0) + 1
        deleted_subjects = {
            s: True
            if count
            >= sum(
                1 for _ in self.interface.old_graph.triples((s, None, None))
            )
            else False
            for s, count in deleted_subjects.items()
        }
        deleted_subjects = set(
            s for s, deleted in deleted_subjects.items() if deleted
        )
        # Get updated subjects.
        updated_subjects = tracker.existing_subjects.difference(
            deleted_subjects
        )
        added_entities = set(
            self.interface.session_new.from_identifier(s)
            for s in added_subjects
        )
        updated_entities = set(
            self.interface.session_new.from_identifier(s)
            for s in updated_subjects
        )
        deleted_entities = set(
            self.interface.session_old.from_identifier(s)
            for s in deleted_subjects
        )
        return added_entities, updated_entities, deleted_entities

    class UnbufferedInterfaceDriver(Store):
        """Provides a read-only view on the interface without the buffers.

        This store implementation provides a read-only view on the connected
        interface without the `InterfaceDriver`'s buffers.
        """

        _driver: "InterfaceDriver"

        # RDFLib
        # ↓ -- ↓

        context_aware: bool = False
        formula_aware: bool = False
        transaction_aware: bool = True
        graph_aware: bool = False

        def __init__(self, *args, driver: "InterfaceDriver", **kwargs):
            """Initialize the store."""
            self._driver = driver
            super().__init__(*args, **kwargs)

        def open(self, configuration: str, create: bool = False) -> None:
            """The interface should be already open. Prevents reopening it."""
            raise ModificationException

        def close(self, commit_pending_transaction=False) -> None:
            """The interface should be open. Prevents closing it."""
            raise ModificationException

        def add(self, triple: Triple, context: Graph, quoted=False) -> None:
            """The view is read-only, prevents modifications."""
            raise ModificationException

        def remove(
            self, triple_pattern: Pattern, context: Optional[Graph] = None
        ) -> None:
            """The view is read-only, prevents modifications."""
            raise ModificationException

        def triples(
            self, triple_pattern: Pattern, context=None
        ) -> Iterator[Tuple[Triple, Graph]]:
            """Yields triples from the interface ignoring the buffers."""
            yield from self._driver.triples(
                triple_pattern, context, ignore_buffers=True
            )

        def __len__(self, context: Graph = None) -> int:
            """Gets the amount of triples on the interface, without buffers."""
            return self._driver.__len__(context, ignore_buffers=True)

        def bind(self, prefix, namespace):
            """Prevents the modification of namespaces."""
            raise ModificationException

        def namespace(self, prefix):
            """Get the namespace to which a prefix is bound."""
            return self._driver.namespace(prefix)

        def prefix(self, namespace):
            """Get a bound namespace's prefix."""
            return self._driver.prefix(namespace)

        def namespaces(self):
            """Get the bound namespaces."""
            return self._driver.namespaces()

        def query(self, *args, **kwargs) -> Result:
            """Perform a SPARQL query on the store."""
            return self._driver.query(*args, **kwargs)

        def update(self, *args, **kwargs):
            """Prevents the modification."""
            raise ModificationException


class Interface(ABC):
    """To be implemented by interface/wrapper developers.

    This is the most generic type of interface.
    """

    # Definition of:
    # Interface
    # ↓ ----- ↓

    disable_entity_tracking: bool = False
    """Whether to disable entity tracking.

    With entity tracking enabled, a list of added, updated and deleted
    entities will be available during commit. If such lists are not
    going to be used, then this property can be set to `True` to
    increase performance.
    """

    root: Optional[Identifier] = None
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

        If you are using a custom base graph (for example based on an RDFLib
        store), please set `self.base = your_graph` within this method.
        Otherwise, an empty base graph will be provided.

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
    def populate(self):
        """Populate the base graph so that it represents the data source.

        This command is run after the data source is opened. Here you are
        expected to populate the base graph so that its information mimics
        the information on the data source, unless you are generating
        triples on the fly. The default session is a session based on the
        base graph.
        """
        pass

    @abstractmethod
    def commit(self):
        """This method commits the changes made by the user.

        Here, you are expected to have access to the following:
        - `self.base`: The base graph (rw). You are not expected to modify it.
        - `self.old_graph`: The old graph (ro).
        - `self.new_Graph`: The new graph (ro).
        - `self.buffer`: The buffer of caught triples (rw) that you now have to
            reflect on the data structures of your software.
        - `self.session_base`: A session based on the base graph (rw). You
            are not expected to modify it.
        - `self.session_old`: A session based on the old graph (ro).
        - `self.session_new`: A session based on the new graph (ro).
        - `self.added`: A list of added entities (rw). You are not expected
            to modify the entities.
        - `self.updated`: A list of updated entities (rw). You are not
            expected to modify the entities.
        - `self.deleted`: A list of deleted entities (rw). You are not
            expected to modify the entities.
        """
        # Examine the differences between the graphs below and make a plan to
        # modify your data structures.

        # Change your data structures below. As you change the data
        # structures, `old_graph` and `new_graph` will change, so do not
        # rely on them. Relying on them would be analogous to changing a
        # dictionary while looping over it.
        pass

    def compute(self, *args, **kwargs):
        """Compute new information (e.g. run a simulation).

        Just compute the new information on the backend and reflect the
        changes on the base graph. The default session is the base session.
        """
        pass

    del compute  # By default not defined.

    # Triplestore methods.

    def add(self, triple: Triple) -> bool:
        """Inspect and control the addition of triples to the base graph.

        Args:
            triple: The triple being added.

        Returns:
            - True: The triple should be added to the base graph.
            - False: The triple should be caught, and therefore not added to
                the base graph. This triple will be latter available during
                commit on the buffer so that the changes that it introduces
                can be translated to the data structure.
        """
        pass

    del add  # By default not defined.

    def remove(self, pattern: Pattern) -> Iterator[Triple]:
        """Inspect and control the removal of triples from the base graph.

        Args:
            pattern: The pattern being removed.

        Returns:
            An iterator with the triples that should be removed from the
            base graph. Any triples not included will not be removed,
            and will be available on the buffer during commit.
        """
        pass

    del remove  # By default not defined.

    def triples(self, pattern: Pattern) -> Iterator[Triple]:
        """Intercept a triple pattern query.

        Can be used to produce triples that do not exist on the base graph
        on the fly.

        Args:
            pattern: The pattern being queried.

        Returns:
            An iterator yielding triples
        """
        pass

    del triples

    # File storage methods.

    def save(self, key: str, file: BinaryIO) -> None:
        """Save a file."""
        pass

    del save  # By default not defined.

    def load(self, key: str) -> BinaryIO:
        """Retrieve a file."""
        pass

    del load  # By default not defined.

    def delete(self, key: str) -> None:
        """Delete a file."""
        pass

    del delete  # By default not defined.

    def hash(self, key: str) -> str:
        """Hash a file."""
        pass

    del hash  # By default not defined.

    def rename(self, key: str, new_key: str) -> None:
        """Rename a file."""
        pass

    del rename  # By default not defined.

    # def query(self, query: str):
    #     """Custom implementation of SPARQL queries for the interface."""
    #     pass
    # del query   # By default not defined.

    # Definition of:
    # Interface
    # ↑ ----- ↑

    # The properties below are set by the driver and accessible on the
    # interface.
    base: Optional[Graph] = None
    old_graph: Optional[Graph] = None
    new_graph: Optional[Graph] = None
    buffer: Optional[Graph] = None

    session_base: Optional[Session] = None
    session_old: Optional[Session] = None
    session_new: Optional[Session] = None
    added: Optional[Set["OntologyEntity"]] = None
    updated: Optional[Set["OntologyEntity"]] = None
    deleted: Optional[Set["OntologyEntity"]] = None
