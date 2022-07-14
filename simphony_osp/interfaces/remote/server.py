"""Implementation of a remote RDFLib store over websockets."""

import io
import json
import logging
import tempfile
from typing import BinaryIO, Callable, Dict, List, Tuple
from uuid import UUID

from rdflib import Graph, URIRef
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf

from simphony_osp.interfaces.interface import Interface
from simphony_osp.interfaces.remote.common import COMMAND
from simphony_osp.interfaces.remote.engine import CommunicationEngineServer

logger = logging.getLogger(__name__)


class InterfaceServer:
    """Receives commands from a client to drive an interface."""

    def __init__(
        self,
        host: str,
        port: int,
        generate_interface: Callable[[str, str], Interface],
    ):
        """Initialize the server."""
        self._engine: CommunicationEngineServer = CommunicationEngineServer(
            host=host,
            port=port,
            handle_request=self.handle_request,
            handle_disconnect=self.handle_disconnect,
        )
        self._interfaces: Dict[UUID, Interface] = dict()
        self._directories: Dict[UUID, tempfile.TemporaryDirectory] = dict()
        self._interface_generator: Callable[
            [str, str], Interface
        ] = generate_interface

    def listen(self) -> None:
        """Listen for connections from clients."""
        self._engine.listen()

    def handle_disconnect(self, connection_id: UUID) -> None:
        """Handle the disconnect of a user. Close and delete his session.

        Args:
            connection_id: The connection that has disconnected.
        """
        if connection_id in self._interfaces:
            self._interfaces[connection_id].close()
            del self._interfaces[connection_id]
        else:
            logger.warning(
                "User %s disconnected, even though it was not "
                "associated with a session." % connection_id
            )

    def handle_request(
        self,
        command: COMMAND,
        data: str,
        files: List[BinaryIO],
        connection_id: UUID,
    ) -> Tuple[str, list]:
        """Handle requests from the client."""
        try:
            if command == COMMAND.OPEN:
                response = self._open(data, connection_id)
            elif command == COMMAND.CLOSE:
                response = self._close(data, connection_id)
            elif command == COMMAND.POPULATE:
                response = self._populate(data, connection_id)
            elif command == COMMAND.COMMIT:
                response = self._commit(data, connection_id)
            elif command == COMMAND.COMPUTE:
                response = self._compute(data, connection_id)
            elif command == COMMAND.ADD:
                response = self._add(data, connection_id)
            elif command == COMMAND.TRIPLES:
                response = self._triples(data, connection_id)
            elif command == COMMAND.REMOVE:
                response = self._remove(data, connection_id)
            elif command == COMMAND.SAVE:
                response = self._save(data, files, connection_id)
            elif command == COMMAND.LOAD:
                response = self._load(data, connection_id)
            elif command == COMMAND.DELETE:
                response = self._delete(data, connection_id)
            elif command == COMMAND.HASH:
                response = self._hash(data, connection_id)
            elif command == COMMAND.RENAME:
                response = self._rename(data, connection_id)
            elif command == COMMAND.STORE_OPEN:
                response = self._store_open(data, connection_id)
            elif command == COMMAND.STORE_CLOSE:
                response = self._store_close(data, connection_id)
            elif command == COMMAND.STORE_ADD:
                response = self._store_add(data, connection_id)
            elif command == COMMAND.STORE_TRIPLES:
                response = self._store_triples(data, connection_id)
            elif command == COMMAND.STORE_REMOVE:
                response = self._store_remove(data, connection_id)
            elif command == COMMAND.STORE_COMMIT:
                response = self._store_commit(data, connection_id)
            elif command == COMMAND.HASATTR:
                response = self._hasattr(data, connection_id)
            elif command == COMMAND.AUTHENTICATE:
                response = self._authenticate(data, connection_id)
            else:
                response = "ERROR: Invalid command", []
            if isinstance(response, str):
                response = response, []
            return response
        except Exception as e:
            logger.error(str(e))
            return ("ERROR: %s: %s" % (type(e).__name__, e)), []

    # Commands

    def _open(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        data = json.loads(data)
        interface.open(**data)
        return json.dumps({COMMAND.OPEN: None})

    def _close(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        interface.close()
        return json.dumps({COMMAND.CLOSE: None})

    def _populate(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        interface.populate()
        return json.dumps({COMMAND.POPULATE: None})

    def _commit(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        interface.commit()
        return json.dumps({COMMAND.COMMIT: None})

    def _compute(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        data = json.loads(data)
        kwargs = data["kwargs"]
        interface.compute(**kwargs)
        return json.dumps({COMMAND.COMPUTE: None})

    def _add(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        graph = json_to_rdf(json.loads(data), Graph())
        for triple in graph:
            interface.add(triple)
        return json.dumps({COMMAND.ADD: None})

    def _remove(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        pattern = next(
            tuple(x if x != URIRef("none:None") else None for x in triple)
            for triple in Graph().parse(io.StringIO(data), format="turtle")
        )
        graph = Graph()
        graph.addN((s, p, o, graph) for s, p, o in interface.remove(pattern))
        return (
            f"{{"
            f'"{COMMAND.REMOVE}": '
            f'{graph.serialize(format="json-ld")}'
            f"}}"
        )

    def _triples(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        pattern = next(
            tuple(x if x != URIRef("none:None") else None for x in triple)
            for triple in Graph().parse(io.StringIO(data), format="turtle")
        )
        graph = Graph()
        graph.addN((s, p, o, graph) for s, p, o in interface.triples(pattern))
        return (
            f"{{"
            f'"{COMMAND.TRIPLES}": '
            f'{graph.serialize(format="json-ld")}'
            f"}}"
        )

    def _save(
        self, data: str, files: List[BinaryIO], connection_id: UUID
    ) -> str:
        interface = self._interfaces[connection_id]
        if hasattr(interface, "save"):
            data = json.loads(data)
            key = data["key"]
            file = files[0]
            interface.save(key, file)
            response = {COMMAND.SAVE: None}
        else:
            response = {COMMAND.NOT_FOUND: True}
        return json.dumps(response)

    def _load(self, data: str, connection_id: UUID) -> (str, List[BinaryIO]):
        interface = self._interfaces[connection_id]
        if hasattr(interface, "load"):
            data = json.loads(data)
            key = data["key"]
            file = interface.load(key)
            response = {COMMAND.LOAD: None}
            return json.dumps(response), [file]
        else:
            response = {COMMAND.NOT_FOUND: True}
            return json.dumps(response), []

    def _delete(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        if hasattr(interface, "delete"):
            data = json.loads(data)
            key = data["key"]
            interface.delete(key)
            response = {COMMAND.DELETE: None}
        else:
            response = {COMMAND.NOT_FOUND: True}
        return json.dumps(response)

    def _hash(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        if hasattr(interface, "delete"):
            data = json.loads(data)
            key = data["key"]
            file_hash = interface.hash(key)
            response = {COMMAND.HASH: file_hash}
        else:
            response = {COMMAND.NOT_FOUND: True}
        return json.dumps(response)

    def _rename(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        if hasattr(interface, "rename"):
            data = json.loads(data)
            key = data["key"]
            new_key = data["new_key"]
            interface.rename(key, new_key)
            response = {COMMAND.RENAME: None}
        else:
            response = {COMMAND.NOT_FOUND: True}
        return json.dumps(response)

    def _store_open(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        data = json.loads(data)
        interface.base.open(**data)
        return json.dumps({COMMAND.STORE_OPEN: None})

    def _store_close(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        data = json.loads(data)
        interface.base.close(**data)
        return json.dumps({COMMAND.STORE_CLOSE: None})

    def _store_add(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        graph = json_to_rdf(json.loads(data), Graph())
        interface.base.addN((s, p, o, interface.base) for s, p, o in graph)
        return json.dumps({COMMAND.STORE_ADD: None})

    def _store_remove(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        patterns = (
            tuple(x if x != URIRef("none:None") else None for x in triple)
            for triple in Graph().parse(io.StringIO(data), format="turtle")
        )
        for pattern in patterns:
            interface.base.remove(pattern)
        return json.dumps({COMMAND.REMOVE: None})

    def _store_triples(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        pattern = next(
            tuple(x if x != URIRef("none:None") else None for x in triple)
            for triple in Graph().parse(io.StringIO(data), format="turtle")
        )
        graph = Graph()
        graph.addN(
            (s, p, o, graph) for s, p, o in interface.base.triples(pattern)
        )
        return (
            f"{{"
            f'"{COMMAND.STORE_TRIPLES}": '
            f'{graph.serialize(format="json-ld")}'
            f"}}"
        )

    def _store_commit(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        interface.base.commit()
        return json.dumps({COMMAND.STORE_COMMIT: None})

    def _hasattr(self, data: str, connection_id: UUID) -> str:
        interface = self._interfaces[connection_id]
        data = json.loads(data)
        attr = data["item"]
        return json.dumps({COMMAND.HASATTR: hasattr(interface, attr)})

    def _authenticate(self, data: str, connection_id: UUID) -> str:
        if connection_id not in self._interfaces:
            data = json.loads(data)
            username, password = data["username"], data["password"]
            self._interfaces[connection_id] = self._interface_generator(
                username, password
            )
        return json.dumps({COMMAND.AUTHENTICATE: None})
