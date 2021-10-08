"""Implementation of a remote RDFLib store over websockets."""

import json
import logging
import shutil
import os

from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple

from rdflib import Graph, URIRef
from rdflib.term import Identifier
from rdflib.store import Store
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf

from osp.core.ontology.cuba import cuba_namespace
from osp.core.session.interfaces.remote.communication_engine import \
    CommunicationEngineServer
from osp.core.session.interfaces.remote.utils import (
    ADD_TRIPLES_COMMAND, COMMIT_COMMAND, DELETE_FILES_COMMAND,
    FETCH_FILES_COMMAND, FETCH_TRIPLES_COMMAND, HASH_FILES_COMMAND,
    LOGIN_COMMAND, REMOVE_TRIPLES_COMMAND, RENAME_FILES_COMMAND,
    ROLLBACK_COMMAND, RUN_COMMAND, UPDATE_FILES_COMMAND, get_hash,
)
from osp.core.utils.general import CUDS_IRI_PREFIX

logger = logging.getLogger(__name__)


class RemoteStoreServer:
    """Implementation of a remote RDFLib store over websockets.

    It consists of a client and a server. The triples are buffered until
    `commit` is called.
    """

    _engine: CommunicationEngineServer
    _store_objects: Dict[Hashable, Store]

    def __init__(self,
                 host: str, port: int,
                 generate_store: Callable,
                 engine_kwargs: Optional[Dict[str, Any]] = None,
                 file_destination: Optional[str] = None,
                 file_uid: bool = True) -> None:
        """Construct the server."""
        self._store_objects = dict()
        self._store_generator = generate_store
        self._file_destination = file_destination
        self._file_uid = file_uid
        if self._file_destination is not None:
            os.makedirs(self._file_destination, exist_ok=True)
        self._engine = CommunicationEngineServer(
            host=host,
            port=port,
            handle_request=self.handle_request,
            handle_disconnect=self.handle_disconnect,
            **(engine_kwargs or dict())
        )
        super().__init__()

    def start(self) -> None:
        """Start the server."""
        self._engine.start_listening()

    def handle_disconnect(self, connection_id: Hashable) -> None:
        """Handle the disconnect of a user. Close and delete his session.

        Args:
            connection_id: The connection that has disconnected.
        """
        if connection_id in self._store_objects:
            self._store_objects[connection_id].close(
                commit_pending_transaction=False)
            del self._store_objects[connection_id]
        else:
            logger.warning("User %s disconnected that was not associated with "
                           "a session" % connection_id)

    def handle_request(self,
                       command: str,
                       data: str,
                       connection_id: Hashable,
                       temp_directory: Optional[str] = None
                       ) -> Tuple[str, list]:
        """Handle requests from the client."""
        try:
            if command == ADD_TRIPLES_COMMAND:
                return self._add(data, connection_id) or '', []
            elif command == REMOVE_TRIPLES_COMMAND:
                return self._remove(data, connection_id) or '', []
            elif command == FETCH_TRIPLES_COMMAND:
                return self._triples(data, connection_id) or '', []
            elif command == COMMIT_COMMAND:
                return self._commit(data, connection_id) or '', []
            elif command == ROLLBACK_COMMAND:
                return self._rollback(data, connection_id) or '', []
            elif command == LOGIN_COMMAND:
                return self._login(data, connection_id) or '', []
            elif command == RUN_COMMAND:
                return self._run(data, connection_id) or '', []
            elif command == DELETE_FILES_COMMAND:
                return self._files_delete(data, connection_id) or '', []
            elif command == RENAME_FILES_COMMAND:
                return self._files_rename(data, connection_id) or '', []
            elif command == HASH_FILES_COMMAND:
                return self._files_hash(data, connection_id) or '', []
            elif command == UPDATE_FILES_COMMAND:
                return self._files_update(data, connection_id,
                                          temp_directory) or '', []
            elif command == FETCH_FILES_COMMAND:
                return self._files_fetch(data, connection_id,
                                         temp_directory)
        except Exception as e:
            logger.error(str(e), exc_info=1)
            return ("ERROR: %s: %s" % (type(e).__name__, e)), []
        return "ERROR: Invalid command", []

    # Commands

    def _files_delete(self,
                      data: str,
                      connection_id: Hashable) -> str:
        if self._file_destination is None:
            raise RuntimeError(f'Not file destination set, cannot execute '
                               f'command {DELETE_FILES_COMMAND}.')
        graph = json_to_rdf(json.loads(data), Graph())
        for identifier, _, path in graph:
            destination = self._compute_real_path(identifier, path)
            try:
                os.remove(destination)
            except FileNotFoundError:
                pass
        return json.dumps({})

    def _files_rename(self,
                      data: str,
                      connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        if self._file_destination is None:
            raise RuntimeError(f'Not file destination set, cannot execute '
                               f'command {RENAME_FILES_COMMAND}.')
        graph = json_to_rdf(json.loads(data), Graph())
        for identifier, _, path in graph:
            destination = self._compute_real_path(identifier, path)
            for (s, p, o), _ in store.triples((identifier,
                                               cuba_namespace.path,
                                               None)):
                source = self._compute_real_path(s, str(o))
                shutil.move(source, destination)
        return json.dumps(dict())

    def _files_hash(self,
                    data: str,
                    connection_id: Hashable) -> str:
        if self._file_destination is None:
            raise RuntimeError(f'Not file destination set, cannot execute '
                               f'command {HASH_FILES_COMMAND}.')
        graph = json_to_rdf(json.loads(data), Graph())
        hashes = []
        for identifier, _, path in graph:
            try:
                hashes += [get_hash(self._compute_real_path(identifier, path))]
            except FileNotFoundError:
                pass
        return json.dumps({"hashes": hashes})

    def _files_update(self,
                      data: str,
                      connection_id: Hashable,
                      temp_directory: Optional[str] = None) -> str:
        if self._file_destination is None:
            raise RuntimeError(f'Not file destination set, cannot execute '
                               f'command {UPDATE_FILES_COMMAND}.')
        graph = json_to_rdf(json.loads(data), Graph())
        for identifier, _, path in graph:
            destination = self._compute_real_path(identifier, path)
            shutil.copy(
                os.path.join(temp_directory, path),
                destination
            )
        return json.dumps(dict())

    def _files_fetch(self,
                     data: str,
                     connection_id: Hashable,
                     temporary_directory: str) -> \
            Tuple[Dict[str, Tuple[str, str]], List[str]]:
        if self._file_destination is None:
            raise RuntimeError(f'Not file destination set, cannot execute '
                               f'command {UPDATE_FILES_COMMAND}.')
        store = self._store_objects[connection_id]
        graph = json_to_rdf(json.loads(data), Graph())
        files = []
        file_names = []
        for identifier, _, _ in graph:
            for (s, p, o), _ in store.triples((identifier,
                                               cuba_namespace.path,
                                               None)):
                source = self._compute_real_path(s, str(o))
                files.append(source)
                file_names.append(str(o))
        # Bug with `await`, statement on line
        # `bytes_data = await socket.recv()`, in function `_decode` in
        # file `communication_engine.py`. When files are downloaded twice
        # from `self._file_destination`, at the second download the `await`
        # command destroys the existing file. This has been debugged
        # adding a method `recv` on the socket object on the websockets library
        # that just prints the content of the folder containing the original
        # file and then calls `recv` on the superclass.
        # As a workaround, we make a copy so that `await` destroys the copy
        # instead of the original file.
        temp_files = []
        for file in files:
            destination = os.path.join(temporary_directory,
                                       os.path.basename(file))
            shutil.copy(file,
                        destination)
            temp_files += [destination]
        return json.dumps(
            {'files': list(zip(temp_files, file_names))}), temp_files

    def _compute_real_path(self,
                           identifier: Identifier,
                           basename: str) -> str:
        path = str(basename)
        if self._file_uid:
            if identifier.startswith(CUDS_IRI_PREFIX):
                path = f"({identifier[len(CUDS_IRI_PREFIX):]}) {path}"
            else:
                safe_identifier = str(identifier) \
                    .replace(':', '_') \
                    .replace('/', '_')
                path = f"({safe_identifier}) {path}"
        return os.path.join(self._file_destination, path)

    def _add(self, data: str, connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        graph = json_to_rdf(json.loads(data), Graph())
        for triple in graph:
            store.add(triple, None)
        return json.dumps(dict())

    def _remove(self, data: str, connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        graph = json_to_rdf(json.loads(data), Graph())
        for triple in graph:
            store.remove(triple, context=None)
        return json.dumps(dict())

    def _triples(self,
                 data: str,
                 connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        pattern = next(
            tuple(x if x != URIRef('none:None') else None for x in triple)
            for triple in json_to_rdf(json.loads(data), Graph())
        )
        graph = Graph()
        for triple, _ in store.triples(pattern):
            graph.add(triple)
        response = {"triples": graph.serialize(format='json-ld')}
        return json.dumps(response)

    def _commit(self,
                data: str,
                connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        store.commit()
        return json.dumps(dict())

    def _rollback(self,
                  data: str,
                  connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        store.rollback()
        return json.dumps(dict())

    def _run(self,
             data: str,
             connection_id: Hashable) -> str:
        store = self._store_objects[connection_id]
        if hasattr(store, 'interface'):
            store.interface.run()
        return json.dumps(dict())

    def _login(self,
               data: str,
               connection_id: Hashable) -> str:
        """Start a new session.

        Args:
            data: The data sent by the user.
            connection_id: The connection_id for the connection that
                requests to start a new session.

        Returns:
            An empty response.
        """
        # If user logs in again, close previous connection.
        if connection_id in self._store_objects:
            self._store_objects[connection_id].close()

        # Allocate new store for the user.
        store_instance = self._store_generator(data)
        self._store_objects[connection_id] = store_instance
        return json.dumps(dict())
