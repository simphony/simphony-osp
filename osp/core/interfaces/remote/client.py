"""Implementation of a remote RDFLib store over websockets."""

import json
import shutil
import tempfile
import os
import urllib.parse
from itertools import chain
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from rdflib import RDF, Graph, Literal, URIRef
from rdflib.store import Store
from rdflib.term import Identifier
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf
from rdflib.plugins.stores.memory import SimpleMemory

from osp.core.interfaces.interface import BufferType
from osp.core.interfaces.remote.communication_engine import \
    CommunicationEngineClient
from osp.core.interfaces.remote.utils import (
    ADD_TRIPLES_COMMAND, COMMIT_COMMAND, DELETE_FILES_COMMAND,
    FETCH_FILES_COMMAND, FETCH_TRIPLES_COMMAND, HASH_FILES_COMMAND,
    LOGIN_COMMAND, REMOVE_TRIPLES_COMMAND, RENAME_FILES_COMMAND,
    UPDATE_FILES_COMMAND, get_hash,
)
from osp.core.utils.cuba_namespace import cuba_namespace
from osp.core.utils.datatypes import Triple, Pattern


class RemoteStoreClient(Store):
    """Implementation of a remote RDFLib store over websockets.

    It consists of a client and a server. The triples are buffered until
    `commit` is called.
    """

    # RDFLib
    # ↓ -- ↓

    transaction_aware = True

    def __init__(self,
                 uri: str = '',
                 connect_kwargs: Optional[Dict[str, Any]] = None,
                 file_destination: Optional[str] = None,
                 *args,
                 configuration_string: str = '',
                 **kwargs) -> None:
        """Construct the remote store client.

        Args:
            uri: WebSocket URI.
            connect_kwargs (dict[str, Any]): Will be passed to
                websockets.connect. E.g. it is possible to pass an SSL context
                with the ssl keyword.
            file_destination: A path to put any uploaded files.
            configuration_string: The configuration string to open the remote
                store.
        """
        # Get URI, username and password.
        uri, username, password = self._parse_uri(uri) if uri else (None, ) * 3
        self._uri = uri
        self._username = username
        self._password = password
        self._auth = None
        self._configuration_string = configuration_string

        self._connect_kwargs = connect_kwargs or dict()

        # Prepare the directories to send and receive files.
        if file_destination is None:
            self.__local_temp_dir = tempfile.TemporaryDirectory()
            self._file_destination = self.__local_temp_dir.name
        else:
            self.__local_temp_dir = None
            self._file_destination = file_destination
            os.makedirs(self._file_destination, exist_ok=True)
        self._local_dir_cache = dict()

        # Create buffers to send triples only on commit.
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}
        super().__init__(*args, **kwargs)

    def open(self, uri: str = '', create: bool = False) -> None:
        """Initializes the communications engine client.

        Args:
            uri: WebSocket URI.
            create: Currently not used, just to comply with RDFLib's API.
        """
        if self._engine is not None:
            self._engine.close()
        if uri:
            uri, username, password = self._parse_uri(uri)
            self._uri = uri
            self._username = username
            self._password = password
            self._auth = None
        self._engine = CommunicationEngineClient(
            uri=self._uri,
            handle_response=self._handle_response,
            **self._connect_kwargs)
        self._engine.send(LOGIN_COMMAND, self._configuration_string)
        # Now download all the files from the server that are not on the client

    def close(self, commit_pending_transaction: bool = False) -> None:
        """Close the connection to the remote store.

        Args:
            commit_pending_transaction: Whether to commit any pending
                transactions before disconnecting.
        """
        if commit_pending_transaction:
            self.commit()
        if self.__local_temp_dir:
            self.__local_temp_dir.cleanup()
        self._engine.close()

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
            triple
            for triple in self._remote_triples(triple_pattern))
        for triple in existing_triples_to_delete:
            self._buffers[BufferType.DELETED].add(triple)

    def triples(self, triple_pattern: Pattern, context=None) \
            -> Iterator[Triple]:
        """Query triples patterns.

        Merges the buffered changes with the data stored on the remote
        store. Therefore, this method involves network traffic.
        """
        # Existing minus added and deleted triples.
        triple_pool = filter(
            lambda x: x not in chain(
                self._buffers[BufferType.DELETED].triples(triple_pattern),
                self._buffers[BufferType.ADDED].triples(triple_pattern)
            ),
            self._remote_triples(triple_pattern))
        # Include added triples (previously they were excluded in order not
        # to duplicate triples).
        triple_pool = chain(
            triple_pool,
            self._buffers[BufferType.ADDED].triples(triple_pattern))
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
        # FILE HANDLING
        # ↓ --------- ↓
        # Detect new files or files whose path changed.
        added_files = dict()
        for s, _, o in self._buffers[BufferType.ADDED].triples(
                (None, cuba_namespace.path, None)):
            if next(self.triples((s, RDF.type, cuba_namespace.File)),
                    None) is not None:
                # File object or path of file for file object changed.
                added_files[s] = o  # Identifier, new_path_local
        # Replace absolute paths with base names in the added buffer.
        for s, path in added_files.items():
            self._buffers[BufferType.ADDED].remove(
                (s, cuba_namespace.path, path)
            )
            self._local_dir_cache[s] = os.path.dirname(path)
            self._buffers[BufferType.ADDED].add(
                (s, cuba_namespace.path,
                 Literal(os.path.basename(str(path)),
                         datatype=path.datatype,
                         lang=path.language))
            )
        # Separate the files whose path changed from the new files.
        updated_files = dict()
        for s in set(added_files.keys()):
            exists = True \
                if next(self._remote_triples((s, RDF.type, None)), None) \
                is not None else False
            if exists:
                updated_files[s] = added_files[s]
                del added_files[s]
        # Detect deleted files
        deleted_files = dict()
        replace_paths = dict()
        for s, _, o in self._buffers[BufferType.DELETED].triples(
                (None, cuba_namespace.path, None)):
            if next(self._remote_triples((s, RDF.type, cuba_namespace.File)),
                    None) is not None:
                # File existed but has been deleted.
                if s not in {**added_files, **updated_files}:
                    deleted_files[s] = o  # Identifier, old_path_local
                    try:
                        del self._local_dir_cache[s]
                    except KeyError:
                        pass
                replace_paths[s] = o

        # Replace absolute paths with base names in the deleted buffer.
        for s, path in replace_paths.items():
            self._buffers[BufferType.DELETED].remove(
                (s, cuba_namespace.path, path)
            )
            self._buffers[BufferType.DELETED].add(
                (s, cuba_namespace.path,
                 Literal(os.path.basename(str(path)),
                         datatype=path.datatype,
                         lang=path.language))
            )

        # Delete the deleted files from the server.
        g = Graph()
        for s, o in deleted_files.items():
            g.add((s, cuba_namespace.path,
                   Literal(os.path.basename(str(o)),
                           datatype=o.datatype,
                           lang=o.language)))
        if len(g) > 0:
            self._engine.send(
                DELETE_FILES_COMMAND,
                g.serialize(format='json-ld')
            )
        # Rename the updated files on the server.
        g = Graph()
        for s, o in updated_files.items():
            g.add((s, cuba_namespace.path,
                   Literal(os.path.basename(str(o)),
                           datatype=o.datatype,
                           lang=o.language)
                   ))
        if len(g) > 0:
            self._engine.send(
                RENAME_FILES_COMMAND,
                g.serialize(format='json-ld')
            )
        # Add the new files to the server, upload the updated files to the
        # server if the hash is different.
        self.upload({**added_files, **updated_files})

        # ↑ --------- ↑
        # FILE HANDLING

        # data are the buffers, serialized (json-ld)
        self._engine.send(
            ADD_TRIPLES_COMMAND,
            self._buffers[BufferType.ADDED].serialize(format='json-ld')
        )
        self._engine.send(
            REMOVE_TRIPLES_COMMAND,
            self._buffers[BufferType.DELETED].serialize(format='json-ld'),
        )
        self._engine.send(COMMIT_COMMAND, '')

        # Clear buffers.
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}

    def rollback(self) -> None:
        """Discard uncommitted changes."""
        self._buffers = {buffer_type: Graph(SimpleMemory())
                         for buffer_type in BufferType}

    # RDFLib
    # ↑ -- ↑

    _engine: CommunicationEngineClient = None
    _local_dir_cache: Dict[Identifier, str]

    def upload(self, files_in_request: Dict[Identifier, Literal]) -> None:
        """Upload a file to the store.

        Args:
            files_in_request: A dict whose keys element are the identifiers
                of the File individuals associated with the files to be
                uploaded. The values hold the paths of the files as RDFLib's
                literals.
        """
        g = Graph()
        for s, o in files_in_request.items():
            g.add((s, cuba_namespace.path,
                   Literal(os.path.basename(str(o)),
                           datatype=o.datatype,
                           lang=o.language)
                   ))
        if len(g) > 0:
            hashes = self._engine.send(
                HASH_FILES_COMMAND,
                g.serialize(format='json-ld')
            )
            files_to_upload = dict()
            for s, o in files_in_request.items():
                file_hash = get_hash(str(o))
                if file_hash not in hashes:
                    files_to_upload[s] = o
            if len(files_to_upload) > 0:
                self._engine.send(UPDATE_FILES_COMMAND,
                                  g.serialize(format='json-ld'),
                                  [str(o) for o in files_to_upload.values()])

    def download(self,
                 *identifiers: Identifier,
                 path: Optional[str] = None) -> None:
        """Download a file from the remote store.

        Args:
            identifiers: The identifiers of the File individuals to fetch
                from the remote store.
            path: A folder to put the downloaded files in. If not folder is
                provided, `self._file_destination` (provided when the class
                was created) is used. If no file destination was provided
                either, then the operation will fail.

        Raises:
             RuntimeError: Neither a path nor a file destination were provided.
        """
        if path is None and self.__local_temp_dir is not None:
            raise RuntimeError("As no file destination was defined for this "
                               "client, a path must be provided when "
                               "calling this function.")
        path = path or self._file_destination
        graph = Graph()
        for identifier in identifiers:
            graph.add((identifier,
                       URIRef('nothing:nothing'),
                       URIRef('nothing:nothing')))
        file_names = self._engine.send(
            FETCH_FILES_COMMAND,
            graph.serialize(format='json-ld')
        )
        if os.path.normpath(path) != os.path.normpath(self._file_destination):
            for file in file_names:
                shutil.move(os.path.join(self._file_destination, file),
                            os.path.join(path, file))

    def _remote_triples(self, triple_pattern: Pattern) -> Iterator[Triple]:
        """Fetch triples from the remote store.

        Args:
            triple_pattern: The triple pattern to query the remote store.
        """
        triple_pattern = tuple(x or URIRef('none:None') for x in
                               triple_pattern)
        pattern = Graph()
        pattern.add(triple_pattern)
        response = self._engine.send(FETCH_TRIPLES_COMMAND,
                                     pattern.serialize(format='json-ld'))

        # Change file paths to absolute paths on the client.
        response = self._filter_triple_iterator_file_handling(response)

        yield from response

    def _filter_triple_iterator_file_handling(self,
                                              response: Iterator[Triple]) \
            -> Iterator[Triple]:
        """Filters the triples so that proper cuba.File paths are shown.

        This filter is applied to the triples from the remote store.
        """
        if self._file_destination is None:
            yield from response
        else:
            is_file = dict()
            for s, p, o in response:
                if p == cuba_namespace.path:
                    if is_file.get(s, None) is None:
                        triple_pattern = (s, RDF.type, cuba_namespace.File)
                        triple_pattern = tuple(x or URIRef('none:None')
                                               for x in triple_pattern)
                        pattern = Graph()
                        pattern.add(triple_pattern)
                        triples = self._engine.send(FETCH_TRIPLES_COMMAND,
                                                    pattern.serialize(
                                                        format='json-ld'))
                        is_file[s] = True \
                            if next(triples, None) is not None else False
                    if is_file[s] and isinstance(o, Literal):
                        path = os.path.basename(str(o))
                        if path.startswith(f"({str(s)}) "):
                            path = path[len(f"({str(s)}) "):]
                        path = os.path.join(
                            self._local_dir_cache.get(s, None)
                            or self._file_destination,
                            path)
                        s, p, o = (s, cuba_namespace.path,
                                   Literal(path,
                                           datatype=o.datatype,
                                           lang=o.language))
                yield s, p, o

    def _handle_response(self,
                         data: str,
                         temp_directory: Optional[str] = None) \
            -> Union[Iterator[Triple], List[str], List[Tuple[str, str]]]:
        data = json.loads(data or '{}')
        """Handle responses from the communications engine server."""
        if ['triples'] == list(data.keys()):
            return (x for x in json_to_rdf(json.loads(data['triples']),
                                           Graph()))
        elif ['hashes'] == list(data.keys()):
            return data['hashes']
        elif ['files'] == list(data.keys()):
            for server_file, basename in data['files']:
                shutil.move(os.path.join(temp_directory, server_file),
                            os.path.join(self._file_destination,
                                         basename))
            return (x[1] for x in data['files'])

    @staticmethod
    def _parse_uri(uri: str) -> Tuple[str, str, str]:
        """Parse the given uri and return uri, username, password.

        Args:
            uri (str): The URI to parse
        """
        if uri is None:
            return None, None, None
        parsed = urllib.parse.urlparse(uri)
        username = parsed.username
        password = parsed.password
        parsed = list(parsed)
        if username or password:
            parsed[1] = parsed[1].split("@")[1]
        uri = urllib.parse.urlunparse(parsed)
        return uri, username, password
