"""Interface API for interface/wrapper developers."""

from abc import ABC, abstractmethod
from enum import IntEnum
from itertools import chain
from typing import Iterable, Iterator, Dict, Optional, TYPE_CHECKING

from rdflib import Graph
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.store import Store
from rdflib.term import Identifier

from osp.core.interfaces.interface import Interface
from osp.core.session import Session
from osp.core.utils.datatypes import Triple, UID

if TYPE_CHECKING:
    from osp.core.ontology import OntologyEntity

__all__ = ["GenericInterfaceStore", "GenericInterface", "BufferType"]


class BufferType(IntEnum):
    """The two types of buffers.

    - ADDED: For triples that have been added.
    - DELETED: For triples that have been deleted.
    """

    ADDED = 0
    DELETED = 1


class GenericInterfaceStore(Store):
    """RDFLib store acting as intermediary between OSP-core and wrappers.

    Offers a triplestore interface for OSP-core to interact with wrappers.

     OSP-core <--> GenericInterfaceStore <--> GenericInterface

    The store is transaction aware (needs commit action to save the changes
    to the wrapper), as it is the only efficient way to provide such a
    triplestore-entity interface (otherwise we have to update an entity
    everytime a single triple from the entity is added).
    """

    interface: "GenericInterface"
    session: Optional['Session'] = None
    _buffers: Dict[BufferType, Graph]

    # RDFLib
    # ↓ -- ↓

    transaction_aware = True
    context_aware = False

    def __init__(self, *args, interface=None, **kwargs):
        """Initialize the InterfaceStore.

        The initialization assigns an interface to the store and creates
        buffers for the store. Then the usual RDFLib's store initialization
        follows.
        """
        if interface is None:
            raise ValueError("No interface provided.")
        self.interface = interface
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}
        super().__init__(*args, **kwargs)

    def open(self, configuration: str, create: bool = False):
        """Asks the interface, to open the data source.

        For now, the create argument is not implemented. The interface is free
        to do whatever it wants in this regard.
        """
        if create:
            raise NotImplementedError
        self.interface.open(configuration)

    def close(self, commit_pending_transaction: bool = False):
        """Tells the interface to close the data source.

        Args:
            commit_pending_transaction: commits uncommitted changes when
            true before closing the data source.
        """
        if commit_pending_transaction:
            self.commit()
        self.interface.close()

    def add(self, triple, context, quoted=False):
        """Adds triples to the store.

        Since the actual addition happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.DELETED]\
            .remove(triple)
        self._buffers[BufferType.ADDED]\
            .add(triple)

    def remove(self, triple_pattern, context=None):
        """Remove triples from the store.

        Since the actual removal happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.ADDED]\
            .remove(triple_pattern)
        existing_triples_to_delete = (
            triple
            for triple in self._interface_triples(triple_pattern))
        for triple in existing_triples_to_delete:
            self._buffers[BufferType.DELETED]\
                .add(triple)

    def triples(self, triple_pattern, context=None):
        """Query triples patterns.

        Merges the buffered changes with the data stored on the interface.
        """
        # Existing minus added and deleted triples.
        triple_pool = filter(
            lambda x: x not in chain(
                self._buffers[BufferType.DELETED].triples(triple_pattern),
                self._buffers[BufferType.ADDED].triples(triple_pattern)
            ),
            self._interface_triples(triple_pattern))
        # Include added triples (previously they were excluded in order not
        # to duplicate triples).
        triple_pool = chain(
            triple_pool,
            self._buffers[BufferType.ADDED].triples(triple_pattern))
        for triple in triple_pool:
            yield triple, iter(())

    def __len__(self, context=None):
        """Get the number of triples in the store.

        For more details, check RDFLib's documentation.
        """
        i = 0
        for _ in self.triples((None, None, None)):
            i += 1
        return i

    def bind(self, prefix, namespace):
        """Bind a namespace to a prefix."""
        raise NotImplementedError

    def namespace(self, prefix):
        """Bind a namespace to a prefix."""
        raise NotImplementedError

    def prefix(self, prefix):
        """Get a bound namespace's prefix."""
        raise NotImplementedError

    def namespaces(self):
        """Get the bound namespaces."""
        raise NotImplementedError

    def query(self, *args, **kwargs):
        """Perform a SPARQL query on the store."""
        return super().query(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Perform a SPARQL update query on the store."""
        return super().update(*args, **kwargs)

    def commit(self):
        """Commit buffered changes."""
        self.session = self.session or Session(store=self)

        # Find out from triples which entities were added, updated and
        # deleted and add their triples to the temporary graph.
        class _ExistenceTracker:
            _interface = self.interface

            def __init__(self):
                self.checked_subjects = set()
                self.existing_subjects = set()

            def __call__(self, subject: Identifier):
                if subject not in self.checked_subjects:
                    self.checked_subjects.add(subject)
                    if next(self._interface.session.graph.triples(
                            (subject, None, None)
                    ), None) is not None:
                        self.existing_subjects.add(subject)

        existence_tracker = _ExistenceTracker()

        # Get added subjects.
        for s, p, o in self._buffers[BufferType.ADDED]\
                .triples((None, None, None)):
            existence_tracker(s)
        added_subjects = existence_tracker.checked_subjects.difference(
            existence_tracker.existing_subjects)
        # Get deleted subjects.
        deleted_subjects = dict()
        for s, p, o in self._buffers[BufferType.DELETED]\
                .triples((None, None, None)):
            existence_tracker(s)
            if (s not in added_subjects and s in
                    existence_tracker.existing_subjects):
                deleted_subjects[s] = deleted_subjects.get(s, 0) + 1
        for s in deleted_subjects.keys():
            i = 0
            for _ in self._interface_triples((s, None, None)):
                i += 1
            if deleted_subjects[s] >= i:
                deleted_subjects[s] = True
            else:
                deleted_subjects[s] = False

        deleted_subjects = set(s
                               for s, deleted in deleted_subjects.items()
                               if deleted)
        # Get updated subjects.
        updated_subjects = existence_tracker.existing_subjects.difference(
            deleted_subjects)

        session = self.session
        # Apply added entities to the engine.
        for entity in (session.from_identifier(s) for s in added_subjects):
            self.interface.add(entity)
        # Apply updated entities to the engine.
        for entity in (session.from_identifier(s) for s in updated_subjects):
            self.interface.update(entity)
        # Apply deleted entities to the engine.
        for s in deleted_subjects:
            self.interface.delete(s)

        # Move the triples from the buffers to the interface's graph.
        for t in self._buffers[BufferType.ADDED].triples((None, None, None)):
            self.interface.graph.add(t)
        for t in self._buffers[BufferType.DELETED].triples((None, None, None)):
            self.interface.graph.remove(t)

        # Clear the buffers.
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}

    def rollback(self):
        """Discard uncommitted changes."""
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}

    # RDFLib
    # ↑ -- ↑

    def _interface_triples(self, triple_pattern) -> Iterable[Triple]:
        """Helper method that gets triples stored in the backend."""
        s, p, o = triple_pattern
        if s is not None:
            triple_iterator = (
                triple
                for entity in filter(
                    lambda x: x is not None, self.interface.load({UID(s)})
                )
                for triple in entity.triples
            )
        else:
            def triple_iterator():
                with self.interface.session:
                    yield from (
                        triple
                        for entity in filter(
                            lambda x: x is not None,
                            self.interface.load(
                                UID(x) for x in
                                self.interface.session.graph.subjects(None,
                                                                      None)
                            ))
                        for triple in entity.triples
                    )

                created_entities = set(self.interface.session.creation_set)
                while created_entities:
                    with self.interface.session:
                        yield from (
                            triple
                            for entity in filter(
                                lambda x: x is not None,
                                self.interface.load(
                                    UID(x) for x in created_entities
                                )
                            )
                            for triple in entity.triples
                        )
                    created_entities = set(self.interface.session.creation_set)
            triple_iterator = triple_iterator()

        triple_iterator = filter(
            lambda x: (x[0] == s if s is not None else True)
            and (x[1] == p if p is not None else True)
            and (x[2] == o if o is not None else True),
            triple_iterator
        )
        yield from triple_iterator


class GenericInterface(ABC, Interface):
    """To be implemented by interface/wrapper developers.

    This is the most general API provided for an interface.
    """

    # Definition of:
    # GenericInterface
    # ↓ ------------ ↓

    @abstractmethod
    def open(self, configuration: str):
        """Open the data source that the interface interacts with.

        You can expect calls to this method even when the data source is
        already open, therefore, an implementation like the following is
        recommended.

        def open(self, configuration: str):
            if your_data_source_is_already_open:
                return
                # To improve the user experience you can check if the
                # configuration string leads to a resource different from
                # the current one and raise an error informing the user.

            # Connect to your data source...
            # your_data_source_is_already_open is for now True.
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
    def apply_added(self, entity: "OntologyEntity") -> None:
        """Receive added ontology entities and apply changes to the backend.

        DO NOT CHANGE the received entity, its information has been set in
        stone by the user already. It belongs to a snapshot of the new
        state, that will be reached when the changes for all entities have
        been applied by you.
        """
        pass

    @abstractmethod
    def apply_updated(self, entity: "OntologyEntity") -> None:
        """Receive updated entities and apply the changes to the backend.

        DO NOT CHANGE the received entity, its information has been set in
        stone by the user already. It belongs to a snapshot of the new
        state, that will be reached when the changes for all entities have
        been applied by you.
        """
        # If you need to compare the new ontology entity with its old version,
        # please uncomment the line below to fetch the old version.
        # old = self.session.from_identifier(entity.identifier)
        pass

    @abstractmethod
    def apply_deleted(self, entity: "OntologyEntity") -> None:
        """Receive deleted entities and apply the changes to the backend.

        DO NOT CHANGE the received entity. It belongs to a snapshot of the
        "old" state, before the user invoked the commit action.
        """
        pass

    @abstractmethod
    def update_from_backend(self,
                            entity: "OntologyEntity") \
            -> Optional["OntologyEntity"]:
        """An entity that you have previously provided is requested.

        You have now to check if the information present on the backend
        matches what you receive, and when not, update the received entity
        to reflect the information from the backend.

        Please, DO CHANGE the received entity.
        """
        pass

    @abstractmethod
    def load_from_backend(self, uid: UID) -> Optional["OntologyEntity"]:
        """An entity that you have NOT previously provided is requested.

        Given it makes logical sense, you have now to look in the backend for
        an entity that would match this `uid`.

        Then construct an ontology entity with such `uid` reflecting the
        information on the backend and return it.

        So please, CREATE a new entity and return it.
        """
        pass

    session: Session
    """Session providing a pre-commit snapshot of the data on the interface.

    You do NOT have to implement this, this is a feature provided to you.

    When the user makes a commit, a chunk of objects are sent to this
    interface, and for each object, one of the functions `apply_added`,
    `apply_updated`, `apply_deleted` is applied. You can use this session on
    on your code to see a snapshot of the data on the interface just before
    the commit was fired. In such way, you can compare the new items with the
    previous ones and apply the changes if your backend provides no way to
    do so.
    """

    # + Methods and properties from definition of: Interface.

    # ↑ ------------ ↑
    # Definition of:
    # GenericInterface

    store_class = GenericInterfaceStore

    def __init__(self, ontology: Optional[Session] = None):
        """Initialize the generic interface."""
        self.session = Session(store=SimpleMemory(),
                               ontology=ontology)
        self.graph = self.session.graph

    def add(self, entity: "OntologyEntity"):
        """Add an entity to the backend."""
        with entity.session:
            self.apply_added(entity)

    def update(self, entity: "OntologyEntity"):
        """Update an entity in the backend."""
        with entity.session:
            self.apply_updated(entity)

    def delete(self, identifier: Identifier):
        """Delete an entity from the backend."""
        with self.session as session:
            entity = session.from_identifier(identifier)
            self.apply_deleted(entity)

    def load(self, uids: Iterable[UID]) -> \
            Iterator[Optional["OntologyEntity"]]:
        """Load an entity from the backend."""
        with self.session as session:
            for uid in uids:
                try:
                    entity = session.from_identifier(uid.to_identifier())
                    yield self.update_from_backend(entity)
                except KeyError:
                    yield self.load_from_backend(uid)
