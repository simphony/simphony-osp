"""Universal interface for wrapper developers."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from base64 import b64encode
from collections.abc import Collection
from datetime import datetime, timedelta
from enum import IntEnum
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Set,
    Tuple,
    Union,
)

from rdflib import RDF, BNode, Graph, URIRef
from rdflib.graph import ModificationException, ReadOnlyGraphAggregate
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.query import Result
from rdflib.store import Store
from rdflib.term import Node

from simphony_osp.session.session import Session
from simphony_osp.utils.datatypes import Pattern, Triple
from simphony_osp.utils.other import take
from simphony_osp.utils.simphony_namespace import simphony_namespace

if TYPE_CHECKING:
    from simphony_osp.ontology.entity import OntologyEntity

__all__ = [
    "BufferType",
    "BufferedSimpleMemoryStore",
    "Interface",
    "InterfaceDriver",
]

logger = logging.getLogger(__name__)


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
        self._buffers[BufferType.ADDED].add(triple)

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
        subclass_method = self.triples
        setattr(self, "triples", super().triples)
        for triple in self._buffers[BufferType.DELETED]:
            super().remove(triple, None)
        setattr(self, "triples", subclass_method)

        # Add triples from added buffer.
        subclass_method = self.add
        setattr(self, "add", super().add)
        super().addN(
            (s, p, o, self._buffers[BufferType.ADDED])
            for s, p, o in self._buffers[BufferType.ADDED]
        )
        setattr(self, "add", subclass_method)

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


class CacheSizeException(RuntimeError):
    """Raised when  triples do not fit in the cache of `InterfaceDriver`."""


class InterfaceDriver(Store):
    """RDFLib store acting as intermediary between SimPhoNy and wrappers.

    Offers a triplestore interface for SimPhoNy to interact with wrappers.

     SimPhoNy <--> InterfaceDriver <--> Interface

    The store is transaction aware (needs a commit action to save the changes
    to the wrapper). Otherwise, one would have to update an entity
    every time a single triple from the entity is added.
    """

    interface: Interface
    """The interface that the driver controls."""

    _buffer_caught: Dict[BufferType, Graph]
    """Holds triples that should not be added to the interface's base graph."""

    _buffer_uncaught: Dict[BufferType, Graph]
    """Holds triples that should be added to the interface's base graph."""

    _queue: Dict[URIRef, Optional[BinaryIO]]
    """Holds handles of files to be uploaded, URIs of files to be deleted."""

    _ontology: Optional[Session]
    """Ontology to be used on the session's shown to the wrapper developer."""

    _cache: Graph
    """Holds cached triples when the interface's cache is enabled."""

    _cached_patterns: Dict[Pattern, datetime]
    """Holds currently cached patterns and the time they were cached."""

    _cache_size: int = 100000
    """Maximum size of the cache in triples."""

    _cache_time: timedelta = timedelta(seconds=0.3)
    """Maximum time to spend in caching after making a request.

    When a request for triples involving a specific subject is made,
    the caching algorithm asks for all the triples involving the subject.
    This call is not subject to a time limit.

    However, in a second stage, if the interface is merely based on a base
    graph (meaning requests can be made using SPARQL), the algorithm will
    also try to cache the children of the such subject, the parent objects,
    and all of its neighbors. Since these operations can take a lot of extra
    time, this parameter fixes a time limit for the cumulative time it
    takes to perform all of these requests. When such caching operations
    take longer than this time, they are interrupted.
    """

    _cache_step: int = 100
    """Number of triples to fetch at once when filling the cache.

    Since SimPhoNy is single-threaded software, the queries described above
    (on the docstring of `_cache_time`) are blocking. This means that if one
    tries to fetch too many items at once from the interface, it may take
    significantly longer than the `_cache_time` to do so, but the operation
    cannot be canceled until all the items have been fetched.

    That is the reason behind this parameter: if it is small enough, one can
    check how long has the caching algorithm been running at smaller
    intervals. Please note that this assumes that asking the interface to
    yield one triple takes a much smaller amount of time than `_cache_time`.
    This is not necessarily always the case (for example if the underlying
    interface produces triples in chunks).
    """

    _file_cache: Optional[TemporaryDirectory] = None
    """Holds files that are accessed while queued.

    Files are queued as byte streams (which can be exhausted). Therefore,
    if a user needs to access a file before it is committed, the byte stream
    needs to be copied somewhere to be committed later. This also applies
    when files need to be accessed during commit by a wrapper (as they are
    truly sent to the wrapper after the `commit` method has finished).
    """

    # RDFLib
    # ↓ -- ↓

    context_aware: bool = False
    formula_aware: bool = False
    transaction_aware: bool = True
    graph_aware: bool = False

    def __init__(
        self,
        *args,
        interface: Interface,
        ontology: Optional[Session] = None,
        **kwargs,
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
        self._cache = Graph("SimpleMemory")
        self._cached_patterns = dict()
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

        # Reset cache
        self._cache.remove((None, None, None))

        # Set-up file bytestream cache
        self._file_cache = TemporaryDirectory()

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
        self.interface.session = session
        try:
            session.lock()
            # Session must not close when exiting its context manager (just
            # in case the user enters the context manager again inside
            # populate).
            with session:
                self.interface.populate()
                session.commit()
        finally:
            session.unlock()
            self.interface.session_base = None
            self.interface.session = None

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Tells the interface to close the data source.

        Args:
            commit_pending_transaction: commits uncommitted changes when
                true before closing the data source.
        """
        if commit_pending_transaction:
            self.commit()
        self.interface.close()

        # Clear the cache
        self._cache.remove((None, None, None))

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

        # Clear bytestream cache
        if self._file_cache is not None:
            self._file_cache.cleanup()
            self._file_cache = None

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

        In addition, this method is responsible for trying to obtain the
        triples from the cache if it is enabled, and for filling it on cache
        misses.
        """
        # Determine source of triples.
        if self.interface.cache and self._cached(triple_pattern):
            query_method = self._cache.triples
            fill_cache, fill_cache_sparql = False, False
        elif hasattr(self.interface, "triples"):
            query_method = self.interface.triples
            fill_cache, fill_cache_sparql = True, False
        else:
            query_method = self.interface.base.triples
            fill_cache, fill_cache_sparql = True, True

        # Manage the triple cache.
        if fill_cache and self.interface.cache:
            """Fill the cache using requests based on triple patterns.

            This stage caches either the requested triple pattern, or if the
            triple pattern contains a subject, all the information about the
            subject.
            """
            timestamp = datetime.now()

            s_p, p_p, o_p = triple_pattern
            if s_p is not None:
                """The requested pattern contains a subject."""
                cache_pattern = (s_p, None, None)
            else:
                """No subject in the triple pattern.

                Cache the triple pattern only.
                """
                cache_pattern = triple_pattern
                fill_cache_sparql = False
            all_triples = set(query_method(cache_pattern))

            def query_method(pattern_triples: Pattern) -> Iterator[Triple]:
                """Filter the retrieved triples.

                Yields only the triples matching the given pattern.
                """
                pat_s, pat_p, pat_o = pattern_triples
                yield from (
                    (a, b, c)
                    for a, b, c in all_triples
                    if all(
                        (
                            pat_s is None or a == pat_s,
                            pat_p is None or b == pat_p,
                            pat_o is None or c == pat_o,
                        )
                    )
                )

            try:
                """Fill the cache with the retrieved triples."""
                self._fill(cache_pattern, all_triples)
            except CacheSizeException:
                """No space for the retrieved triples. No action."""
                pass

            if fill_cache_sparql:
                """Fill the cache using requests based on SPARQL.

                This stage allows additional triples related to the children of
                the object, the parent object and the neighbors to be cached.
                """
                base = self.interface.base

                if not isinstance(s_p, BNode):
                    queries = (
                        f"""SELECT ?s ?p ?o WHERE {{
                            <{s_p}> ?predicate ?s .
                            ?s ?p ?o .
                        }}""",  # request info about children
                        f"""SELECT ?s ?p ?o WHERE {{
                        ?s ?predicate <{s_p}> .
                        ?s ?p ?o .
                        }}""",  # request info about parent
                        f"""SELECT ?s ?p ?o WHERE {{
                        ?parent ?predicate <{s_p}> .
                        ?parent ?another_predicate ?s .
                        ?s ?p ?o .
                        }}""",  # request info about neighbors
                    )
                else:
                    queries = tuple()

                start = datetime.now()
                for query in queries:
                    query_iterator = iter(
                        base.query(
                            query,
                            initNs={
                                "owl": URIRef("http://www.w3.org/2002/07/owl#")
                            },
                        )
                    )

                    result = set()
                    taken = True
                    timeout = False
                    while taken and not timeout:
                        taken = set(take(query_iterator, self._cache_step))
                        result |= taken

                        if datetime.now() - start > self._cache_time:
                            timeout = True
                            break

                    if timeout:
                        break

                    result = set(result)
                    if self._compute_space(older_than=timestamp) >= len(
                        result
                    ):
                        pattern_dict = dict()
                        for s, p, o in result:
                            pattern_dict[(s, None, None)] = pattern_dict.get(
                                (s, None, None), set()
                            ) | {(s, p, o)}

                        for pattern, triples in pattern_dict.items():
                            self._fill(pattern, triples)

        # Pool existing triples minus added and deleted triples.
        triple_pool = query_method(triple_pattern)
        if not ignore_buffers:
            triple_pool = (
                triple
                for triple in triple_pool
                if all(
                    triple not in graph
                    for graph in (
                        self._buffer_uncaught[BufferType.DELETED],
                        self._buffer_caught[BufferType.DELETED],
                        self._buffer_uncaught[BufferType.ADDED],
                        self._buffer_caught[BufferType.ADDED],
                    )
                )
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
        if self.interface.entity_tracking:
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
        self.interface.session = session
        try:
            session.lock()
            with session:
                self.interface.commit()
        finally:
            session.unlock()
            self.interface.session_new = None
            self.interface.session = None

        # Copies the uncaught triples from the buffers to the base graph.
        for triple in self._buffer_uncaught[BufferType.DELETED]:
            self.interface.base.remove(triple)
        self.interface.base.addN(
            (s, p, o, self.interface.base)
            for s, p, o in self._buffer_uncaught[BufferType.ADDED]
        )
        self.interface.base.commit()

        # Queue file upload and removal for file objects.
        for s in chain(
            self._buffer_uncaught[BufferType.DELETED][
                : RDF.type : simphony_namespace.File
            ],
            self._buffer_caught[BufferType.DELETED][
                : RDF.type : simphony_namespace.File
            ],
        ):
            self.queue(s, None)
        for URI, file in self._queue.items():
            if file is None:
                if hasattr(self.interface, "delete"):
                    self.interface.delete(URI)
                else:
                    logging.warning(
                        f"Ignoring deletion of file {URI}, as the session "
                        f"does not support deleting files."
                    )
            else:
                if hasattr(self.interface, "save"):
                    self.interface.save(URI, file)
                else:
                    logging.warning(
                        f"File {URI}, will NOT be committed to the session, "
                        f"as it does not support the storage of new files."
                    )
                file.close()

        # Reflect changes from buffers in the cache.
        if self.interface.cache:
            # - remove deleted triples
            for triple in chain(
                self._buffer_uncaught[BufferType.DELETED],
                self._buffer_caught[BufferType.DELETED],
            ):
                self._cache.remove(triple)
            # - add the added triples
            timestamp = datetime.now()
            cacheable_triples = dict()
            for triple in chain(
                self._buffer_uncaught[BufferType.ADDED],
                self._buffer_caught[BufferType.ADDED],
            ):
                compatible_cached_patterns = self._compatible_patterns(
                    triple
                ) & set(self._cached_patterns)
                for pattern in compatible_cached_patterns:
                    cacheable_triples[pattern] = cacheable_triples.get(
                        pattern, set()
                    ) | {triple}
            for pattern, triples in cacheable_triples.items():
                try:
                    self._fill(
                        pattern, triples, older_than=timestamp, replace=False
                    )
                except CacheSizeException:
                    self._cache.remove(pattern)
                    try:
                        del self._cached_patterns[pattern]
                    except KeyError:
                        pass

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

    def compute(
        self,
        **kwargs: Union[
            str,
            int,
            float,
            bool,
            None,
            Iterable[Union[str, int, float, bool, None]],
        ],
    ):
        """Compute new information (e.g. run a simulation)."""
        if not hasattr(self.interface, "compute"):
            raise AttributeError(
                f"'{self.interface}' object has no attribute 'compute'"
            )

        self.commit()

        self.interface.session_base = Session(
            base=self.interface.base, ontology=self._ontology
        )
        session = self.interface.session_base
        self.interface.session = session
        try:
            session.lock()
            with session:
                self.interface.compute(**kwargs)
                session.commit()
        finally:
            session.unlock()
            self.interface.session_base = None
            self.interface.session = None

    def queue(self, key: URIRef, file: Optional[BinaryIO]) -> None:
        """Queue a file to be committed."""
        if not hasattr(self.interface, "save"):
            logger.warning(
                "This session does not support saving new files. The "
                "contents of the file will NOT be saved during the commit "
                "operation."
            )

        # Clear cached bytestream
        file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")
        file_path = Path(self._file_cache.name) / file_name
        if file_path.exists():
            file_path.unlink()

        self._queue[key] = file

    def load(self, key: URIRef) -> BinaryIO:
        """Retrieve a file."""
        if key in self._queue:
            file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")

            # Save a temporary copy of the file and put a file handle
            # pointing to the copy on the queue
            if not (Path(self._file_cache.name) / file_name).exists():
                queued = self._queue[key]
                with open(
                    Path(self._file_cache.name) / file_name, "wb"
                ) as file:
                    file.write(queued.read())

                file = open(Path(self._file_cache.name) / file_name, "rb")
                self._queue[key] = file

            # Return a file handle pointing to the copy
            byte_stream = open(Path(self._file_cache.name) / file_name, "rb")
        elif hasattr(self.interface, "load"):
            byte_stream = self.interface.load(key)
        else:
            raise FileNotFoundError(
                "This session does not support file storage. Unable to "
                "retrieve the file contents."
            )

        return byte_stream

    def cache_clear(self):
        """Clear the interface's cache."""
        self._cache.remove((None, None, None))
        self._cached_patterns.clear()

    def _compute_entity_modifications(
        self,
    ) -> Tuple[Set[OntologyEntity], Set[OntologyEntity], Set[OntologyEntity]]:

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
        deleted_subjects = {
            s for s, deleted in deleted_subjects.items() if deleted
        }
        # Get updated subjects.
        updated_subjects = tracker.existing_subjects.difference(
            deleted_subjects
        )
        added_entities = {
            self.interface.session_new.from_identifier(s)
            for s in added_subjects
        }
        updated_entities = {
            self.interface.session_new.from_identifier(s)
            for s in updated_subjects
        }
        deleted_entities = {
            self.interface.session_old.from_identifier(s)
            for s in deleted_subjects
        }
        return added_entities, updated_entities, deleted_entities

    class UnbufferedInterfaceDriver(Store):
        """Provides a read-only view on the interface without the buffers.

        This store implementation provides a read-only view on the connected
        interface without the `InterfaceDriver`'s buffers.
        """

        _driver: InterfaceDriver

        # RDFLib
        # ↓ -- ↓

        context_aware: bool = False
        formula_aware: bool = False
        transaction_aware: bool = True
        graph_aware: bool = False

        def __init__(self, *args, driver: InterfaceDriver, **kwargs):
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

    def _fill(
        self,
        triple_pattern: Pattern,
        triples: Collection[Triple],
        older_than: Optional[datetime] = None,
        replace: bool = True,
    ) -> None:
        """Fill the cache with new triples.

        Args:
            triples: An collection of triples to fill the cache with.
            triple_pattern: The triple pattern that is being updated.
            older_than: Cache entries older than this date can be cleared
                to make room for the new triples. When not specified,
                `datetime.now()` is invoked.

        Raises:
            CacheSizeException: No space left on the cache to fill it with
            the provided triples.
        """
        if older_than is None:
            older_than = datetime.now()

        """Check if there is room for the new triples.

        Also compute the patterns that should be removed to make room for
        the new one.
        """
        if len(triples) > self._cache_size:
            """The triples to store are bigger than the cache."""
            raise CacheSizeException()
        elif len(triples) > (self._cache_size - len(self._cache)):
            """Not enough free space in the cache.

            Find out which cached patterns can be removed to make room for
            the new triples.
            """
            to_remove = set()
            removable_patterns = dict()
            # sub-patterns of the pattern to cache are always removable
            removable_patterns.update(
                {
                    pattern: None
                    for pattern in set(self._cached_patterns)
                    - {triple_pattern}
                    if self._is_sub_pattern(pattern, triple_pattern)
                }
            )
            if replace:
                removable_patterns.update({triple_pattern: None})
            to_remove |= set(removable_patterns)
            # concatenate the rest of the patterns:
            # TODO: do not sort, keep ordering when inserting
            removable_patterns.update(
                {
                    pattern: date
                    for pattern, date in sorted(
                        self._cached_patterns.items(), key=lambda x: x[1]
                    )
                    if date < older_than
                }
            )
            triple_count = 0
            for pattern in removable_patterns:
                triple_count += sum(1 for _ in self._cache.triples(pattern))
                to_remove.add(pattern)
                if triple_count >= len(triples):
                    break
            else:
                raise CacheSizeException()

            """Remove the patterns to make room for the new one."""
            for pattern in to_remove:
                self._cache.remove(pattern)
                try:
                    del self._cached_patterns[pattern]
                except KeyError:
                    pass

        """Fill the cache with the new pattern."""
        self._cache.remove(triple_pattern)
        self._cache.addN((s, p, o, self._cache) for s, p, o in triples)
        self._cached_patterns[triple_pattern] = datetime.now()

    def _compute_space(
        self,
        older_than: Optional[datetime] = None,
    ) -> int:
        """Compute the free space on the cache.

        Args:
            older_than: Consider patterns cached more recently than this
                date as pinned.

        Returns:
            Free space on the cache (in triples).
        """
        if older_than is None:
            older_than = datetime.now()

        patterns = {
            pattern
            for pattern, date in self._cached_patterns.items()
            if date < older_than
        }
        triple_count = 0
        for pattern in patterns:
            triple_count += sum(1 for _ in self._cache.triples(pattern))

        return min(
            self._cache_size,
            self._cache_size - len(self._cache) + triple_count,
        )

    @staticmethod
    def _is_sub_pattern(sub_pattern: Pattern, pattern: Pattern) -> bool:
        """Determine whether a triple pattern is a sub-pattern of another.

        Args:
            sub_pattern: The pattern that is assumed to be a sub-pattern.
            pattern: The pattern that is assumed to be the super-pattern.

        Returns:
            Whether the above assumptions are true or not.
        """
        return all(
            sub_pattern[i] == pattern[i] or pattern[i] is None
            for i in range(0, 3)
        )

    @staticmethod
    def _compatible_patterns(triple: Triple) -> Set[Pattern]:
        """List the patterns that are compatible with a given triple."""
        s, p, o = triple
        return {
            (s, p, o),
            (s, p, None),
            (None, p, o),
            (s, None, o),
            (None, None, o),
            (s, None, None),
            (None, p, None),
            (None, None, None),
        }

    def _cached(self, item: Pattern) -> bool:
        """Determine whether a given pattern is already cached."""
        return bool(
            self._compatible_patterns(item) & set(self._cached_patterns)
        )


class Interface(ABC):
    """To be implemented by interface/wrapper developers.

    This is the most generic type of interface.
    """

    # Definition of:
    # Interface
    # ↓ ----- ↓

    base: Optional[Graph] = None
    """A base graph can be provided by the wrapper developer."""

    entity_tracking: bool = True
    """Whether to enable entity tracking.

    With entity tracking enabled, a list of added, updated and deleted
    entities will be available during commit. If such lists are not
    going to be used, then this property can be set to `False` to
    increase performance.
    """

    cache: bool = False
    """Whether to enable caching.

    When caching is enabled, the number of calls to the methods of the
    interface are reduced. This is useful if the latency of such calls is
    high. This is the case, for example,
    """

    def __init__(
        self,
        **kwargs: Union[
            str,
            int,
            float,
            bool,
            None,
            Iterable[Union[str, int, float, bool, None]],
        ],
    ):
        """Initialize the wrapper.

        The `__init__` method accepts JSON-serializable keyword arguments
        in order to let the user configure parameters of the wrapper that
        are not configurable via the ontology. For example, the type of
        solver used by a simulation engine.

        Save such parameters to private attribute to use them later (e.g.
        in the `open` method).

        Args:
            kwargs: JSON-serializable keyword arguments that contain no
                nested JSON objects (check the type hint for this argument).
        """
        super().__init__()

    @abstractmethod
    def open(
        self,
        configuration: str,
        create: bool = False,
    ) -> None:
        """Open the data source that the wrapper interacts with.

        You can expect calls to this method even when the data source is
        already accesible, therefore, an implementation similar to the one
        below is recommended.

        >>> def open(self, configuration: str, create: bool = False):
        >>>    if your_data_source_is_already_open:
        >>>        return
        >>>        # To improve the user experience you can check if the
        >>>        # configuration string leads to a resource different from
        >>>        # the current one and raise an error informing the user.
        >>>
        >>>    # Connect to your data source...
        >>>    # your_data_source_is_already_open is for now True.

        If you are using a custom base graph, please set
        `self.base = your_graph` within this method. Otherwise, an empty base
        graph will be created instead.

        Args:
            configuration: Used to locate or configure the data source to be
                opened.
            create: Whether the data source should be created if it does not
                exist. When false, if the data source does not exist, you
                should raise an exception. When true, create an empty data
                source.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the data source that the interface interacts with.

        This method should NOT commit uncommitted changes.

        This method should close the connection that was obtained in `open`,
        and free any locked up resources.

        You can expect calls to this method even when the data source is
        already closed. Therefore, an implementation like the following is
        recommended.

        >>> def close(self):
        >>>    if your_data_source_is_already_closed:
        >>>        return
        >>>
        >>>    # Close the connection to your data source.
        >>>    # your_data_source_is_already_closed is for now True
        """
        pass

    @abstractmethod
    def populate(self) -> None:
        """Populate the base session so that it represents the data source.

        This command is run after the data source is opened. Here you are
        expected to populate the base graph so that its information mimics
        the information on the data source, unless you are generating
        triples on the fly using the `triples` method. The default session
        inside this method is a session based on the base graph.

        The base graph is available on `self.base`, and a session based on
        the base graph is available on `self.session` and `self.session_base`.
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """This method commits the changes made by the user.

        Within this method, you have access to the following resources:

        - `self.base`: The base graph (rw). You are not expected to modify it.
        - `self.old_graph`: The old graph (ro).
        - `self.new_graph`: The new graph (ro).
        - `self.buffer`: The buffer of triples caught by `add` and `remove`
          (rw) that you now have to reflect on the data structures of your
          software.
        - `self.session_base`: A session based on the base graph (rw). You are
          not expected to modify it.
        - `self.session_old`: A session based on the old graph (ro).
        - `self.session_new`: A session based on the new graph (ro).
        - `self.session`: same as `self.session_new`.
        - `self.added`: A list of added individuals (rw). You are not expected
          to modify the entities.
        - `self.updated`: A list of updated individuals (rw). You are not
          expected to modify the entities.
        - `self.deleted`: A list of deleted individuals (rw). You are not
          expected to modify the entities.

        Before updating the data structures, check that the changes provided
        by the user do not leave them in a consistent state. This necessary
        because SimPhoNy cannot revert the changes you make to your
        data structures. Raise an AssertionError if the check fails.

        Raises:
            AssertionError: When the data provided by the user would produce
                an inconsistent or unpredictable state of the data structures.
        """
        # Examine the differences between the graphs below and make a plan to
        # modify your data structures.

        # Change your data structures below. As you change the data
        # structures, `old_graph` and `new_graph` will change, so do not
        # rely on them. Relying on them would be analogous to changing a
        # dictionary while looping over it.
        pass

    def compute(
        self,
        **kwargs: Union[
            str,
            int,
            float,
            bool,
            None,
            Iterable[Union[str, int, float, bool, None]],
        ],
    ) -> None:
        """Compute new information (e.g. run a simulation).

        Compute the new information on the backend and reflect the changes on
        the base graph. The default session is the base session.

        The base graph is available on `self.base`, and a session based on
        the base graph is available on `self.session` and `self.session_base`.
        """
        pass

    # Triplestore methods.

    def add(self, triple: Triple) -> bool:
        """Inspect and control the addition of triples to the base graph.

        Args:
            triple: The triple being added.

        Returns:
            True when the triple should be added to the base graph. False when
            the triple should be caught, and therefore not added to the base
            graph. This triple will be latter available during commit on the
            buffer so that the changes that it introduces can be translated to
            the data structure.
        """
        pass

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

    # File storage methods.

    def save(self, key: str, file: BinaryIO) -> None:
        """Save a file.

        Read the bytestream offered as a file handle and save the contents
        somewhere, associating them with the provided key for later retrieval.

        Args:
            key: Identifier of the individual associated with the file.
            file: File (as a file-like object) to be saved.
        """
        pass

    def load(self, key: str) -> BinaryIO:
        """Retrieve a file.

        Provide a file handle associated with the provided key.

        Args:
            key: Identifier of the individual associated with the file.

        Returns:
            File handle associated with the provided key.
        """
        pass

    def delete(self, key: str) -> None:
        """Delete a file.

        Delete the file associated with the provided key.

        Args:
            key: Identifier of the individual associated with the file.
        """
        pass

    def hash(self, key: str) -> str:
        """Hash a file."""
        pass

    def rename(self, key: str, new_key: str) -> None:
        """Rename a file."""
        pass

    # The properties below are set by the driver and accessible on the
    # interface. They are not meant to be set by the developers.
    old_graph: Optional[Graph] = None
    new_graph: Optional[Graph] = None
    buffer: Optional[Graph] = None

    session_base: Optional[Session] = None
    session_old: Optional[Session] = None
    session_new: Optional[Session] = None
    session: Optional[Session] = None
    added: Optional[Set[OntologyEntity]] = None
    updated: Optional[Set[OntologyEntity]] = None
    deleted: Optional[Set[OntologyEntity]] = None

    # Definition of:
    # Interface
    # ↑ ----- ↑

    def __getattribute__(self, name: str):
        """Return getattr(self, name)."""
        if name in {
            "compute",
            "add",
            "remove",
            "triples",
            "save",
            "load",
            "delete",
            "hash",
            "rename",
        } and getattr(type(self), name) is getattr(Interface, name):
            raise AttributeError(name)
        return super().__getattribute__(name)
