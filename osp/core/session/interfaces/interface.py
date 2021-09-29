"""Interface API for interface/wrapper developers."""

from abc import ABC, abstractmethod
from enum import IntEnum
from itertools import chain
from typing import Iterable, Dict, Optional, Set, TYPE_CHECKING

from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.store import Store
from rdflib.term import Identifier

from osp.core.ontology.datatypes import Triple, UID
from osp.core.session.session import Session

if TYPE_CHECKING:
    from osp.core.ontology import OntologyEntity

__all__ = ["InterfaceStore", "Interface"]


class BufferType(IntEnum):
    """The two types of buffers.

    - ADDED: For triples that have been added.
    - DELETED: For triples that have been deleted.
    """

    ADDED = 0
    DELETED = 1


class InterfaceStore(Store):
    """RDFLib store acting as intermediary between OSP-core and wrappers.

    Offers a triplestore interface to OSP-core and an entity interface to
    the wrappers.

    The store is transaction aware (needs commit action to save the changes
    to the wrapper), as it is the only efficient way to provide such a
    triplestore-entity interface (otherwise we have to update an entity
    everytime a single triple from the entity is added).
    """

    transaction_aware = True

    _interface: "Interface"

    _buffers: Dict[BufferType, SimpleMemory]

    def __init__(self, *args, interface=None, **kwargs):
        """Initialize the InterfaceStore.

        The initialization assigns an interface to the store and creates
        buffers for the store. Then the usual RDFLib's store initialization
        follows.
        """
        if interface is None:
            raise ValueError("No interface provided.")
        if not isinstance(interface, Interface):
            raise TypeError(
                "Object provided as interface is not an interface.")
        self._interface = interface
        self._buffers = {buffer_type: SimpleMemory()
                         for buffer_type in BufferType}
        super().__init__(*args, **kwargs)

    def open(self, configuration: str, create: bool = False):
        """Asks the interface, to open the data source.

        For now, the create argument is not implemented. The interface is free
        to do whatever it wants in this regard.
        """
        if create:
            raise NotImplementedError
        self._interface.open(configuration)

    def close(self, commit_pending_transaction: bool = False):
        """Tells the interface to close the data source.

        Args:
            commit_pending_transaction: commits uncommitted changes when
            true before closing the data source.
        """
        if commit_pending_transaction:
            self.commit()
        self._interface.close()

    def add(self, triple, context, quoted=False):
        """Adds triples to the store.

        Since the actual addition happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.DELETED]\
            .remove(triple, context=context)
        self._buffers[BufferType.ADDED]\
            .add(triple, context, quoted=quoted)

    def remove(self, triple_pattern, context=None):
        """Remove triples from the store.

        Since the actual removal happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.ADDED]\
            .remove(triple_pattern, context=context)
        existing_triples_to_delete = (
            triple
            for triple in self._interface_triples(triple_pattern))
        for triple in existing_triples_to_delete:
            self._buffers[BufferType.DELETED]\
                .add(triple, context, quoted=False)

    def triples(self, triple_pattern, context=None):
        """Query triples patterns.

        Merges the buffered changes with the data stored on the interface.
        """
        # Existing minus added and deleted triples.
        triple_pool = filter(
            lambda x: x not in chain(
                (x for x, _ in self._buffers[BufferType.DELETED]
                    .triples(triple_pattern, context=context)),
                (x for x, _ in self._buffers[BufferType.ADDED]
                 .triples(triple_pattern, context=context))
            ),
            self._interface_triples(triple_pattern))
        # Include added triples (previously they were excluded in order not
        # to duplicate triples).
        triple_pool = chain(
            triple_pool,
            (triple for triple, _ in self._buffers[BufferType.ADDED]
                .triples(triple_pattern, context=context)))
        for triple in triple_pool:
            yield triple, iter(())

    def _interface_triples(self, triple_pattern) -> Iterable[Triple]:
        """Helper method that gets triples stored in the backend."""
        s, p, o = triple_pattern
        if s is None:
            # self._wrapper.load_everything_from_backend()
            # yield from self._wrapper.session.graph.triples((s, p, o))
            raise NotImplementedError("Every query to a backend must involve a"
                                      "subject.")
        else:
            yield from self._interface.load({s})

    def __len__(self, context=None):
        """Get the number of triples in the store.

        For more details, check RDFLib's documentation.
        """
        raise NotImplementedError

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
        # Create a temporary session to store ontology entities.
        session = Session()

        # Find out from triples which entities were added, updated and
        # deleted and add their triples to the temporary graph.
        class _ExistenceTracker:
            _interface = self._interface

            def __init__(self):
                self.checked_subjects = set()
                self.existing_subjects = set()

            def __call__(self, subject: Identifier):
                if subject not in self.checked_subjects:
                    self.checked_subjects.add(subject)
                    if self._interface.load({s}):
                        self.existing_subjects.add(s)

        existence_tracker = _ExistenceTracker()

        # Get added subjects.
        for (s, p, o), _ in self._buffers[BufferType.ADDED]\
                .triples((None, None, None), context=None):
            existence_tracker(s)
            session.graph.add((s, p, o))
        added_subjects = existence_tracker.checked_subjects.difference(
            existence_tracker.existing_subjects)
        # Get deleted subjects.
        deleted_subjects = set()
        for (s, p, o), _ in self._buffers[BufferType.DELETED]\
                .triples((None, None, None), context=None):
            existence_tracker(s)
            if (s not in added_subjects and s in
                    existence_tracker.existing_subjects):
                deleted_subjects.add(s)
        # Get updated subjects.
        updated_subjects = existence_tracker.existing_subjects.difference(
            deleted_subjects)
        # Fill session with triples from the backend for the updated
        # and deleted subjects.
        for s in updated_subjects | deleted_subjects:
            for triple in self._interface_triples((s, None, None)):
                session.graph.add(triple)

        # Send the added entities to the wrapper.
        for entity in (session.from_identifier(s) for s in added_subjects):
            self._interface.apply_added(entity)
        # Send the updated entities to the wrapper.
        for entity in (session.from_identifier(s) for s in updated_subjects):
            self._interface.apply_updated(entity)
        # Send the deleted entities to the wrapper.
        for entity in (session.from_identifier(s) for s in deleted_subjects):
            self._interface.apply_deleted(entity)

        # Clear buffers.
        self._buffers = {buffer_type: SimpleMemory()
                         for buffer_type in BufferType}

    def rollback(self):
        """Discard uncommitted changes."""
        self._buffers = {buffer_type: SimpleMemory()
                         for buffer_type in BufferType}


class Interface(ABC):
    """To be implemented by interface/wrapper developers.

    This is the most general API provided for an interface.
    """

    root: Optional[Identifier] = None
    store_class = InterfaceStore

    @abstractmethod
    def apply_added(self, entity: "OntologyEntity") -> None:
        """Receive added ontology entities and apply changes to the backend."""
        pass

    @abstractmethod
    def apply_updated(self, entity: "OntologyEntity") -> None:
        """Receive updated entities and apply the changes to the backend."""
        pass

    @abstractmethod
    def apply_deleted(self, entity: "OntologyEntity") -> None:
        """Receive deleted entities and apply the changes to the backend."""
        pass

    @abstractmethod
    def _load_from_backend(self, uid: UID) -> Optional["OntologyEntity"]:
        """Load the entity with the specified uid from the backend.

        When the element cannot be found, it should return None.
        """
        pass

    @abstractmethod
    def open(self, configuration: str):
        """Open the data source that the interface interacts with."""
        pass

    @abstractmethod
    def close(self):
        """Close the data source that the interface interacts with.

        This method should NOT commit uncommitted changes.
        """
        pass

    def load(self, identifiers: Iterable[Identifier]) -> Set[Triple]:
        """Load multiple ontology entities from the backend.

        This method encapsulates _load_from_backend. Note that it is not an
        abstract method, and this is it not meant to be implemented by the
        interface developer.

        It basically sets a new session where items loaded from the backend
        are to be stored, so that the interface developer does not have to
        worry about it. Once all the entities have been spawned,
        their triples are returned.

        Args:
            identifiers: the identifiers of the entities that are to be loaded.

        Returns:
            Triples describing the ontology entities provided by the backend.
        """
        with Session():
            triples = set()
            entities = (
                self._load_from_backend(UID(x))
                for x in identifiers)
            for entity in entities:
                if entity is not None:
                    triples |= set(entity.triples)
        return triples
