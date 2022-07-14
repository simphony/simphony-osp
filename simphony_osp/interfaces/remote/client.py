"""Implementation of a remote RDFLib store over websockets."""

import json
import os
import tempfile
from itertools import chain
from typing import (
    Any,
    BinaryIO,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Union,
)

from rdflib import Graph, URIRef
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf
from rdflib.plugins.stores.memory import SimpleMemory
from rdflib.store import Store

from simphony_osp.interfaces.interface import BufferType, Interface
from simphony_osp.interfaces.remote.common import COMMAND, parse_uri
from simphony_osp.interfaces.remote.engine import CommunicationEngineClient
from simphony_osp.utils.datatypes import Pattern, Triple


class RemoteInterface(Interface):
    """Interface that communicates with a remote interface server."""

    # Connection and authentication.
    _uri: Optional[str] = None
    _username: Optional[str] = None
    _password: Optional[str] = None
    _engine: Optional[CommunicationEngineClient] = None

    @staticmethod
    def _handle_response(
        data: str, files: List[BinaryIO]
    ) -> (Dict[str, Any], List[BinaryIO]):
        data = json.loads(data or "{}")
        return data, files

    def __getattribute__(self, item):
        """Check whether the interface on the remote side has the attribute."""
        if item in (
            "compute",
            "add",
            "remove",
            "triples",
            "save",
            "load",
            "delete",
            "hash",
            "rename",
        ):
            response, _ = self._engine.send(
                COMMAND.HASATTR, json.dumps({"item": item})
            )
            if response[COMMAND.HASATTR] is False:
                raise AttributeError(item)
        return super().__getattribute__(item)

    # Interface
    # ↓ ----- ↓

    entity_tracking = False

    cache = True

    def open(self, configuration: str, create: bool = False) -> None:
        """Implements the OPEN command."""
        if self._engine is not None:
            raise RuntimeError(
                f"Already connected to {self._uri}. Please "
                f"close the session first."
            )

        # Decode configuration string.
        uri, username, password = (
            parse_uri(configuration) if configuration else (None,) * 3
        )
        self._uri, self._username, self._password = uri, username, password

        self._engine = CommunicationEngineClient(
            uri=self._uri,
            handle_response=self._handle_response,
        )

        # Send authentication command
        response, _ = self._engine.send(
            COMMAND.AUTHENTICATE,
            json.dumps(
                {"username": self._username, "password": self._password}
            ),
        )

        if self.base is None:
            remote_store = RemoteStoreClient(engine=self._engine)
            self.base = Graph(store=remote_store)

        # response, _ = self._engine.send(
        #     COMMAND.OPEN,
        #     json.dumps({
        #         "configuration": configuration,
        #         "create": create
        #     }),
        # )
        # return response[COMMAND.OPEN]

    def close(self) -> None:
        """Implements the CLOSE command."""
        if self._engine is None:
            return

        # response, _ = self._engine.send(
        #     COMMAND.CLOSE,
        #     json.dumps({}),
        # )

        # Close connection and clear connection information.
        self._engine.close()
        self._uri, self._username, self._password = (None,) * 3

        # return response[COMMAND.CLOSE]

    def populate(self) -> None:
        """Implements the POPULATE command."""
        response, _ = self._engine.send(
            COMMAND.POPULATE,
            json.dumps({}),
        )
        return response[COMMAND.POPULATE]

    def commit(self) -> None:
        """Implements the ROOT command."""
        response, _ = self._engine.send(
            COMMAND.COMMIT,
            json.dumps({}),
        )
        return response[COMMAND.COMMIT]

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
        """Implements the COMPUTE command."""
        response, _ = self._engine.send(
            COMMAND.COMPUTE,
            json.dumps({"kwargs": kwargs}),
        )
        return response.get(COMMAND.COMPUTE)

    def add(self, triple: Triple) -> bool:
        """Implements the ADD command."""
        g = Graph()
        g.add(triple)
        response, _ = self._engine.send(
            COMMAND.ADD,
            json.dumps(g.serialize(format="json-ld")),
        )
        return response.get(COMMAND.ADD)

    def remove(self, pattern: Triple) -> Iterator[Triple]:
        """Implements the REMOVE command."""
        g = Graph()
        s = pattern[0] if pattern[0] is not None else URIRef("none:None")
        p = pattern[1] if pattern[1] is not None else URIRef("none:None")
        o = pattern[2] if pattern[2] is not None else URIRef("none:None")
        g.add((s, p, o))
        response, _ = self._engine.send(
            COMMAND.REMOVE,
            g.serialize(format="turtle"),
        )
        yield from json_to_rdf(response[COMMAND.REMOVE], Graph())

    def triples(self, pattern: Triple) -> Iterator[Triple]:
        """Implements the TRIPLES command."""
        g = Graph()
        s = pattern[0] if pattern[0] is not None else URIRef("none:None")
        p = pattern[1] if pattern[1] is not None else URIRef("none:None")
        o = pattern[2] if pattern[2] is not None else URIRef("none:None")
        g.add((s, p, o))
        response, _ = self._engine.send(
            COMMAND.TRIPLES,
            g.serialize(format="turtle"),
        )
        yield from json_to_rdf(response[COMMAND.TRIPLES], Graph())

    def save(self, key: str, file: BinaryIO) -> None:
        """Implements the SAVE command."""
        file = tempfile.NamedTemporaryFile(delete=False)
        try:
            response, _ = self._engine.send(
                COMMAND.COMPUTE,
                json.dumps(
                    {
                        "key": key,
                    }
                ),
                [file.name],
            )
        finally:
            os.remove(file.name)
        return response.get(COMMAND.SAVE)

    def load(self, key: str) -> BinaryIO:
        """Implements the LOAD command."""
        response, files = self._engine.send(
            COMMAND.LOAD,
            json.dumps(
                {
                    "key": key,
                }
            ),
        )
        return files

    def delete(self, key: str) -> BinaryIO:
        """Implements the DELETE command."""
        response, _ = self._engine.send(
            COMMAND.DELETE,
            json.dumps(
                {
                    "key": key,
                }
            ),
        )
        return response[COMMAND.DELETE]

    def hash(self, key: str) -> str:
        """Implements the HASH command."""
        response, _ = self._engine.send(
            COMMAND.HASH,
            json.dumps(
                {
                    "key": key,
                }
            ),
        )
        return response[COMMAND.HASH]

    def rename(self, key: str, new_key: str) -> None:
        """Implements the RENAME command."""
        response, _ = self._engine.send(
            COMMAND.RENAME,
            json.dumps(
                {
                    "key": key,
                }
            ),
        )
        return response[COMMAND.RENAME]

    # Interface
    # ↑ ----- ↑


class RemoteStoreClient(Store):
    """Implementation of a remote RDFLib store over websockets.

    It consists of a client and a server. The triples are buffered until
    `commit` is called.
    """

    # Connection and authentication.
    _engine: Optional[CommunicationEngineClient] = None

    # RDFLib
    # ↓ -- ↓

    transaction_aware = True
    graph_aware = False
    context_aware = False
    formula_aware = False

    def __init__(
        self,
        configuration: Optional[str] = None,
        identifier: Optional[URIRef] = None,
        engine: CommunicationEngineClient = None,
    ) -> None:
        """Construct the remote store client."""
        if engine is None:
            raise ValueError("No engine provided.")
        self._engine = engine
        self._reset_buffers()  # Creates the buffers for the first time.
        super().__init__(configuration, identifier)

    def open(self, configuration: str, create: bool = False) -> None:
        """Initializes the communications engine client.

        Args:
            configuration: WebSocket URI.
            create: Currently not used, just to comply with RDFLib's API.
        """
        self._reset_buffers()
        response, _ = self._engine.send(
            COMMAND.STORE_OPEN,
            json.dumps({"configuration": configuration, "create": create}),
        )
        return response[COMMAND.STORE_OPEN]

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Close the connection to the remote store.

        Args:
            commit_pending_transaction: Whether to commit any pending
                transactions before disconnecting.
        """
        response, _ = self._engine.send(
            COMMAND.STORE_CLOSE,
            json.dumps(
                {"commit_pending_transaction": commit_pending_transaction}
            ),
        )
        return response[COMMAND.STORE_CLOSE]

    def add(self, triple: Triple, context, quoted=False) -> None:
        """Adds triples to the store.

        Since the actual addition happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.DELETED].remove(triple)
        self._buffers[BufferType.ADDED].add(triple)

    def remove(self, triple_pattern: Pattern, context=None) -> None:
        """Remove triples from the store.

        Since the actual removal happens during a commit, this method just
        buffers the changes.
        """
        self._buffers[BufferType.ADDED].remove(triple_pattern)
        existing_triples_to_delete = (
            triple for triple in self._remote_triples(triple_pattern)
        )
        for triple in existing_triples_to_delete:
            self._buffers[BufferType.DELETED].add(triple)

    def triples(
        self, triple_pattern: Pattern, context=None
    ) -> Iterator[Triple]:
        """Query triples patterns.

        Merges the buffered changes with the data stored on the remote
        store. Therefore, this method involves network traffic.
        """
        # Existing minus added and deleted triples.
        triple_pool = filter(
            lambda x: x
            not in chain(
                self._buffers[BufferType.DELETED].triples(triple_pattern),
                self._buffers[BufferType.ADDED].triples(triple_pattern),
            ),
            self._remote_triples(triple_pattern),
        )
        # Include added triples (previously they were excluded in order not
        # to duplicate triples).
        triple_pool = chain(
            triple_pool,
            self._buffers[BufferType.ADDED].triples(triple_pattern),
        )
        for triple in triple_pool:
            yield triple, iter(())

    def __len__(self, context=None) -> int:
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

    def commit(self) -> None:
        """Commit buffered changes."""
        # data are the buffers, serialized (json-ld)
        self._engine.send(
            COMMAND.STORE_ADD,
            self._buffers[BufferType.ADDED].serialize(format="json-ld"),
        )
        self._engine.send(
            COMMAND.STORE_REMOVE,
            self._buffers[BufferType.DELETED].serialize(format="turtle"),
        )
        self._engine.send(COMMAND.STORE_COMMIT, "")

        self._reset_buffers()

    def rollback(self) -> None:
        """Discard uncommitted changes."""
        self._reset_buffers()

    # RDFLib
    # ↑ -- ↑

    def _remote_triples(self, triple_pattern: Pattern) -> Iterator[Triple]:
        """Fetch triples from the remote store.

        Args:
            triple_pattern: The triple pattern to query the remote store.
        """
        triple_pattern = tuple(
            x or URIRef("none:None") for x in triple_pattern
        )
        pattern = Graph()
        pattern.add(triple_pattern)
        response, _ = self._engine.send(
            COMMAND.STORE_TRIPLES, pattern.serialize(format="turtle")
        )
        yield from json_to_rdf(response[COMMAND.STORE_TRIPLES], Graph())

    def _reset_buffers(self) -> None:
        """Replaces the existing buffers by empty buffers."""
        self._buffers = {
            buffer_type: Graph(SimpleMemory()) for buffer_type in BufferType
        }
