"""Interface between the SimPhoNy OSP and SQLAlchemy."""

from enum import IntEnum
from typing import Dict, Iterator, Optional

from rdflib import Graph, URIRef
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.term import Identifier

from osp.core.interfaces.triplestore import TriplestoreInterface
from osp.core.utils.datatypes import Triple, Pattern


class BufferType(IntEnum):
    """Enum of triple buffer types.

    Currently, the `rdflib-sqlalchemy` plugin is not transaction-aware,
    even though the store in the plug-in is labeled as such. The `commit`
    and `rollback` methods do nothing. Therefore, a buffer of added triples
    and a buffer of removed triples are implemented to provide this
    capability.

    - ADDED: For triples that have been added.
    - DELETED: For triples that have been deleted.
    """

    ADDED = 0
    DELETED = 1


class SQLAlchemyInterface(TriplestoreInterface):
    """An interface to an SQL database using SQLAlchemy."""

    _identifier: Identifier = URIRef('http://www.osp-core.com/SQLAlchemy')
    """The identifier of the graph serving as context of the saved triples."""

    _graph: Optional[Graph] = None
    """Representation of the contents of the database as an RDFLib graph
    using the `rdflib-sqlalchemy` plug-in."""

    _uri: Optional[str] = None
    """SQLAlchemy URI used to connect to the database."""

    _buffers: Optional[Dict[BufferType, Graph]]
    """Triple buffers (see docstring of `BufferType`)."""

    def __init__(self) -> None:
        """Initialize the interface."""
        self._reset_buffers()
        super().__init__()

    def _reset_buffers(self) -> None:
        """Reset the contents of the buffers."""
        self._buffers = {buffer_type: Graph(SimpleMemory(),
                                            identifier=self._identifier)
                         for buffer_type in BufferType}

    def _graph_triples(self, pattern: Pattern) -> Iterator[Triple]:
        """Yield triples from the RDFLib graph connected to the database."""
        yield from self._graph.triples(pattern)

    # TriplestoreInterface
    # ↓ ---------------- ↓

    root: Optional[Identifier] = None

    def triples(self, pattern: Pattern) -> Iterator[Triple]:
        """Query the store for triples matching the provided pattern.

        Args:
            pattern: The triple pattern to query.

        Returns:
            Iterator of triples compatible with query pattern.
        """
        if self._graph is None:
            raise RuntimeError('No database was loaded.')

        yield from self._buffers[BufferType.ADDED].triples(pattern)
        yield from filter(lambda x: not (
            x in self._buffers[BufferType.ADDED]
            or x in self._buffers[BufferType.DELETED]
        ), self._graph.triples(pattern))

    def add(self, *triples: Triple) -> None:
        """Add the provided triples to the store.

        Args:
            triples: The triples to add to the triplestore.
        """
        for triple in triples:
            self._buffers[BufferType.DELETED] \
                .remove(triple)

        quads = map(lambda t: (t[0], t[1], t[2],
                               self._buffers[BufferType.ADDED]),
                    triples)
        self._buffers[BufferType.ADDED] \
            .addN(quads)

    def remove(self, pattern: Pattern) -> None:
        """Remove triples matching the pattern from the triplestore.

        Args:
            pattern: Any triples from the triplestore matching this pattern
                will be deleted.
        """
        self._buffers[BufferType.ADDED] \
            .remove(pattern)
        existing_triples_to_delete = (
            triple
            for triple in self._graph_triples(pattern))
        for triple in existing_triples_to_delete:
            self._buffers[BufferType.DELETED] \
                .add(triple)

    def rollback(self) -> None:
        """Discard uncommitted changes to the triple store."""
        self._reset_buffers()
        # Should use the code below, but so far it does nothing (not
        #  implemented on `rdflib-sqlalchemy`).
        # self._graph.rollback()

    def commit(self):
        """Commit pending changes to the triple store."""
        for triple in self._buffers[BufferType.DELETED]:
            self._graph.remove(triple)
        quads = map(lambda t: (t[0], t[1], t[2],
                               self._graph),
                    self._buffers[BufferType.ADDED])
        self._graph.addN(quads)
        self._reset_buffers()
        # Should use the code below, but so far it does nothing (not
        #  implemented on `rdflib-sqlalchemy`).
        # self._graph.commit()

    def open(self, configuration: str, create: bool = False):
        """Open a connection to the database.

        Args:
            configuration: The SQLAlchemy URI pointing to the database to
                which the user wishes to connect.
            create: Whether to create the database file if it does not exist.
        """
        # TODO: Create databases if create is `True`.
        if self._uri is not None and self._uri != configuration:
            raise RuntimeError(f'A different project database {self._uri}'
                               f'is already open!')

        self._graph = Graph("SQLAlchemy", identifier=self._identifier)
        self._graph.open(configuration, create=True)
        self._uri = configuration
        self._reset_buffers()

    def close(self) -> None:
        """Close the connection to the database."""
        if self._graph is not None:
            self._reset_buffers()
            self._graph.close(commit_pending_transaction=False)
            self._uri = None
            self._graph = None

    # ↑ ---------------- ↑
