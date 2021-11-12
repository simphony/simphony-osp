"""A session connecting to a backend which stores the CUDS in triples."""

from abc import ABC, abstractmethod
from typing import Iterator

from osp.core.ontology.datatypes import Pattern, Triple
from osp.core.session.interfaces.interface import Interface
from osp.core.session.interfaces.generic import GenericInterfaceStore


class TriplestoreStore(GenericInterfaceStore):
    """RDFLib store, communicates with the TripleStoreInterface."""

    interface: "TriplestoreInterface"

    def __init__(self, *args, interface=None, **kwargs):
        """Initialize the TriplestoreStore."""
        super().__init__(*args, interface=interface, **kwargs)
        # TODO: Do not create the buffers in the first place.
        del self._buffers

    def add(self, triple, context, quoted=False):
        """Adds triples to the store."""
        self.interface.add(triple)

    def remove(self, triple_pattern, context=None):
        """Remove triples from the store."""
        self.interface.remove(triple_pattern)

    def triples(self, triple_pattern, context=None):
        """Query triples patterns."""
        for triple in self.interface.triples(triple_pattern):
            yield triple, iter(())

    def commit(self):
        """Commit buffered changes."""
        self.interface.commit()

    def rollback(self):
        """Discard uncommitted changes."""
        self.interface.rollback()


class TriplestoreInterface(ABC, Interface):
    """A session connecting to a backend which stores the CUDS in triples."""

    # Definition of:
    # TriplestoreInterface
    # ↓ ---------------- ↓

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
    def commit(self) -> None:
        """Commit pending changes to the triple store.

        Usually, you have a similar method on your database connection
        object (that one should get in `open`) that you can just call.
        """
        pass

    @abstractmethod
    def rollback(self):
        """Discard uncommitted changes to the triple store.

        Usually, you have a similar method on your database connection
        object (that one should get in `open`) that you can just call.
        """
        pass

    @abstractmethod
    def open(self, configuration: str):
        """Open a connection to the triplestore.

        You can expect calls to this method even when the triplestore is
        already open, therefore, an implementation like the following is
        recommended.

        def open(self, configuration: str):
            if your_triplestore_is_already_open:
                return
                # To improve the user experience you can check if the
                # configuration string leads to a resource different from
                # the current one and raise an error informing the user.

            # Connect to your triplestore and get a connection/engine object...
            # your_triplestore_is_already_open is for now True.
        """
        pass

    @abstractmethod
    def close(self):
        """Close the connection to the triplestore.

        This method should NOT commit uncommitted changes.

        This method should close the connection that was obtained in `open`,
        and free any locked up resources.

        You can expect calls to this method even when the triplestore is
        already closed. Therefore, an implementation like the following is
        recommended.

        def close(self):
            if your_triplestore_is_already_closed:
                return

            # Close the connection to your triplestore.
            # your_triplestore_is_already_closed is for now True
        """

    # + Methods and properties from definition of: Interface.

    # ↑ ---------------- ↑
    # Definition of:
    # TriplestoreInterface

    store_class = TriplestoreStore

    def __init__(self):
        """Initialize the TripleStoreInterface."""
        super().__init__()
        # TODO: Do not create the session in the first place.
        self.session = None
