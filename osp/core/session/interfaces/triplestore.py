"""A session connecting to a backend which stores the CUDS in triples."""

from abc import abstractmethod
from typing import Iterator, Optional, TYPE_CHECKING

from osp.core.ontology.datatypes import Pattern, Triple, UID
from osp.core.session.interfaces.interface import Interface, InterfaceStore

if TYPE_CHECKING:
    from osp.core.ontology import OntologyEntity


class TriplestoreStore(InterfaceStore):
    """RDFLib store, communicates with the TripleStoreInterface."""

    transaction_aware = True

    _interface: "TriplestoreInterface"

    def __init__(self, *args, interface=None, **kwargs):
        """Initialize the TriplestoreStore."""
        if interface is None:
            raise ValueError("No interface provided.")
        if not isinstance(interface, Interface):
            raise TypeError(
                "Object provided as interface is not an interface.")
        # TODO: Do not create the buffers in the first place.
        super().__init__(*args, interface=interface, **kwargs)
        del self._buffers

    def add(self, triple, context, quoted=False):
        """Adds triples to the store."""
        self._interface.add(triple)

    def remove(self, triple_pattern, context=None):
        """Remove triples from the store."""
        self._interface.remove(triple_pattern)

    def triples(self, triple_pattern, context=None):
        """Query triples patterns."""
        for triple in self._interface.triples(triple_pattern):
            yield triple, iter(())

    def commit(self):
        """Commit buffered changes."""
        self._interface.commit()

    def rollback(self):
        """Discard uncommitted changes."""
        self._interface.rollback()


class TriplestoreInterface(Interface):
    """A session connecting to a backend which stores the CUDS in triples."""

    store_class = TriplestoreStore

    @abstractmethod
    def triples(self, pattern: Pattern) -> Iterator[Triple]:
        """Query the store for triples matching the provided pattern."""
        pass

    @abstractmethod
    def add(self, *triples: Triple) -> Iterator[Triple]:
        """Add the provided triples to the store."""
        pass

    @abstractmethod
    def remove(self, pattern: Pattern) -> Iterator[Triple]:
        """Remove triples matching the provided pattern from the store."""
        pass

    @abstractmethod
    def commit(self):
        """Commit changes to the triple store."""
        pass

    @abstractmethod
    def rollback(self):
        """Discard uncommitted changes to the triple store."""
        pass

    def open(self, configuration: str):
        """Open the triplestore."""
        pass

    def close(self):
        """Close the triplestore."""
        pass

    def apply_added(self, entity: "OntologyEntity") -> None:
        """Receive added ontology entities and apply changes to the backend."""
        self.add(*entity.triples)

    def apply_updated(self, entity: "OntologyEntity") -> None:
        """Receive updated entities and apply the changes to the backend."""
        self.remove((entity.identifier, None, None))
        self.add(*entity.triples)

    def apply_deleted(self, entity: "OntologyEntity") -> None:
        """Receive deleted entities and apply the changes to the backend."""
        self.remove((entity.identifier, None, None))

    def _load_from_backend(self, uid: UID) \
            -> Optional["OntologyEntity"]:
        """Load the entity with the specified uid from the backend.

        When the element cannot be found, it should return None.
        """
        raise NotImplementedError
