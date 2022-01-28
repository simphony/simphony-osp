"""A session connecting to a backend which stores the CUDS in triples."""

from abc import ABC, abstractmethod
from typing import Iterable, Iterator, Dict, Optional, Set, TYPE_CHECKING, \
    Tuple

from rdflib import Graph
from rdflib.query import Result
from rdflib.store import Store
from rdflib.term import Identifier

from osp.core.interfaces.interface import Interface, Driver
from osp.core.interfaces.overlay import OverlayInterface, OverlayDriver
from osp.core.session import Session
from osp.core.utils.datatypes import Pattern, Triple


class TriplestoreDriver(Driver):
    """RDFLib store, communicates with the TriplestoreInterface."""

    interface: 'TriplestoreInterface'

    # RDFLib
    # ↓ -- ↓

    context_aware = False
    formula_aware = False
    transaction_aware = True
    graph_aware = False

    def __init__(self,
                 *args,
                 interface: 'TriplestoreInterface',
                 **kwargs):
        """Initialize the OverlayDriver.

        The initialization assigns an interface to the store. Then the usual
        RDFLib's store initialization follows.
        """
        if not isinstance(interface, TriplestoreInterface):
            raise ValueError("No valid interface provided.")
        self.interface = interface
        self.interface.close()

        super().__init__(*args, interface=interface, **kwargs)

    def open(self, configuration: str, create: bool = False) -> None:
        """Asks the interface to open the data source."""
        self.interface.open(configuration, create)

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Tells the interface to close the data source.

        Args:
            commit_pending_transaction: commits uncommitted changes when
                true before closing the data source.
        """
        if commit_pending_transaction:
            self.commit()
        self.interface.close()

    def add(self, triple: Triple, context: Graph, quoted=False) -> None:
        """Adds triples to the store."""
        self.interface.add(triple)

    def remove(self,
               triple_pattern: Pattern,
               context: Optional[Graph] = None) -> None:
        """Remove triples from the store."""
        self.interface.remove(triple_pattern)

    def triples(self,
                triple_pattern: Pattern,
                context=None) -> Iterator[Tuple[Triple, Graph]]:
        """Query triple patterns."""
        for triple in self.interface.triples(triple_pattern):
            yield triple, iter(())

    def __len__(self, context: Graph = None) -> int:
        """Get the number of triples in the store."""
        return sum(1 for _ in self.triples((None, None, None)))

    def bind(self, *args, **kwargs):
        """Bind a namespace to a prefix."""
        return super().bind(*args, **kwargs)

    def namespace(self, *args, **kwargs):
        """Bind a namespace to a prefix."""
        return super().namespace(*args, **kwargs)

    def prefix(self, *args, **kwargs):
        """Get a bound namespace's prefix."""
        return super().prefix(*args, **kwargs)

    def namespaces(self):
        """Get the bound namespaces."""
        return super().namespaces()

    def query(self, *args, **kwargs) -> Result:
        """Perform a SPARQL query on the store."""
        return super().query(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Perform a SPARQL update query on the store."""
        return super().update(*args, **kwargs)

    def commit(self):
        """Commit buffered changes."""
        self.interface.commit()

    def rollback(self):
        """Discard uncommitted changes."""
        self.interface.rollback()

    # RDFLib
    # ↑ -- ↑


class TriplestoreInterface(ABC, Interface):
    """A session connecting to a backend which stores the CUDS in triples."""

    # Definition of:
    # TriplestoreInterface
    # ↓ ---------------- ↓

    root: Optional[Identifier] = None
    """Define a custom root object.

    When defined, the user will get this specific ontology entity when invoking
    the wrapper (instead of a virtual container). This is however of little
    interest for a triplestore interface.
    """

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

    # ↑ ---------------- ↑
    # Definition of:
    # TriplestoreInterface

    driver = TriplestoreDriver
