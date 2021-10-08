"""Utilities used in the communication for the remote stores."""

import asyncio
import hashlib
import logging
import math
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, \
    Tuple, Union

import websockets
import websockets.exceptions as ws_exceptions


logger = logging.getLogger(__name__)

BLOCK_SIZE = 4096
LEN_FILES_HEADER = [5]  # num_blocks
LEN_HEADER = [2, 5, 2]  # version, num_blocks, num_files
VERSION = 1
DEBUG_MAX = 1000


def decode_header(bytestring: bytes, lengths: List[int]) -> Union[int, str]:
    """Decode the header given as a string of bytes.

    Args:
        bytestring: The encoded header
        lengths: The number of bytes for the individual components

    Yields:
        Interpret all elements that have a corresponding length as int. If
            there are leftover bytes decode them using utf-8.
    """
    i = 0
    for length in lengths:
        if i + length > len(bytestring):
            raise IndexError("Length mismatch in header")
        yield int.from_bytes(bytestring[i: i + length], byteorder="big")
        i += length
    if len(bytestring) > i:
        yield bytestring[i:].decode("utf-8")


def encode_header(elements: Union[int, str], lengths) -> bytes:
    """Encode the header to single array of bytes.

    Args:
        elements: The elements to encode. All but the last
                                    must be int. The last one can be str.
        lengths ([type]): The number of bytes in the encoded header.

    Raises:
        ValueError: elements and lengths mismatch in number of elements
        NotImplementedError: Invalid datatype in elements.

    Returns:
        bytes: The encoded header
    """
    r = b""
    if len(lengths) > len(elements) or len(elements) > len(lengths) + 1:
        raise ValueError
    for element, length in zip(elements, lengths):
        if not isinstance(element, int):
            raise NotImplementedError
        r += element.to_bytes(length=length, byteorder="big")
    if len(elements) > len(lengths):
        if not isinstance(elements[-1], str):
            raise NotImplementedError("Invalid type of %s" % elements[-1])
        r += elements[-1].encode("utf-8")
    return r


def split_message(msg: str, block_size: int = BLOCK_SIZE):
    """Split the message to send in small blocks.

    Args:
        msg: The message to send.
        block_size: The size of the blocks.
                                    Defaults to BLOCK_SIZE.

    Returns:
        int, Generator: Number of blocks, Generator over blocks.
    """
    msg = msg.encode("utf-8")
    num_blocks = int(math.ceil(len(msg) / block_size))

    def gen(msg, num_blocks, block_size):
        for i in range(num_blocks):
            logger.debug("Sending message block %s of %s"
                         % (i + 1, num_blocks))
            yield msg[i * block_size: (i + 1) * block_size]
        logger.debug("Done")
    return num_blocks, gen(msg, num_blocks, block_size)


async def join_message(websocket, num_blocks: int) -> str:
    """Get the message that was decomposed in different blocks.

    Args:
        websocket: wecksocket object to receive the objects.
        num_blocks: The number of blocks that belong to the message.

    Returns:
        str: The data, decoded using utf-8.
    """
    data = b""
    for i in range(num_blocks):
        logger.debug("Receiving message block %s of %s"
                     % (i + 1, num_blocks))
        data += await websocket.recv()
    logger.debug("Done")
    data = data.decode("utf-8")
    return data


def encode_files(files: List[str]) -> bytes:
    """Encode the files to be sent to over the networks.

    Will send file in several blocks.

    Args:
        files: A list of paths to send.

    Yields:
        bytes: The bytes of the file
    """
    logger.debug("Will send %s files" % len(files))
    for i, file in enumerate(files):
        filename = os.path.basename(file)
        num_blocks = int(math.ceil(os.path.getsize(file) / BLOCK_SIZE))
        logger.debug("Send file %s (%s of %s) with %s block(s) of %s bytes"
                     % (file, i + 1, len(files), num_blocks, BLOCK_SIZE))
        yield encode_header([num_blocks, filename], LEN_FILES_HEADER)

        # send the file contents
        with open(file, "rb") as f:
            for i, block in enumerate(iter(lambda: f.read(BLOCK_SIZE), b"")):
                logger.debug("Send file block %s of %s" % (i + 1, num_blocks))
                yield block
            logger.debug("Done")


async def receive_files(num_files: int,
                        websocket,
                        directory: str,
                        file_hashes: Optional[Dict[str, str]] = None):
    """Will receive and store the files sent to the websocket.

    Args:
        num_files: The number of files to load.
        websocket: The websocket to load the files from.
        directory: The location to store the files.
        file_hashes: Hashes of files of already received files.
    """
    if file_hashes is None:
        file_hashes = dict()
    for i in range(num_files):
        logger.debug("Load file %s of %s" % (i + 1, num_files))
        num_blocks, filename = decode_header(await websocket.recv(),
                                             LEN_FILES_HEADER)
        filename = os.path.basename(filename)
        file_hashes[filename] = hashlib.sha256()
        file_path = os.path.join(directory, filename)
        logger.debug("Storing file %s with %s blocks."
                     % (file_path, num_blocks))
        with open(file_path, "wb") as f:
            for j in range(num_blocks):
                logger.debug("Receive block %s of %s" % (j + 1, num_blocks))
                data = await websocket.recv()
                file_hashes[filename].update(data)
                f.write(data)
            logger.debug("Done")
        file_hashes[filename] = file_hashes[filename].hexdigest()


class CommunicationEngineServer:
    """Server side of the CommunicationEngine.

    The communication engine manages the connection between the remote and
    a local side. The server will be executed on the remote side.
    """

    def __init__(self,
                 host: str,
                 port: int,
                 handle_request: Callable,
                 handle_disconnect: Callable,
                 **kwargs: dict[str, Any]) -> None:
        """Construct the communication engine's server.

        Args:
            host (str): The hostname.
            port (int): The port.
            handle_request: Handles the requests of the user.
                Signature: command(str), data(str), temp_directory(str),
                    user(UUID).
            handle_disconnect: Gets called when a user disconnects.
                Signature: UUID(user).
            kwargs (dict[str, Any]): Will be passed to websockets.connect.
                E.g. it is possible to pass an SSL context with the ssl
                keyword.
        """
        self.host = host
        self.port = port
        self.kwargs = kwargs
        self._handle_request = handle_request
        self._handle_disconnect = handle_disconnect
        self._file_hashes = dict()
        self._connection_ids = dict()

    def start_listening(self) -> None:
        """Start the server on given host + port."""
        event_loop = asyncio.get_event_loop()
        start_server = websockets.serve(self._serve, self.host, self.port,
                                        **self.kwargs)
        event_loop.run_until_complete(start_server)
        event_loop.run_forever()

    async def _serve(self, socket, _: str) -> None:
        """Wait for requests, compute responses and serve them to the user.

        Args:
            socket: The websockets object.
            _: The path of the URI (will be ignored).
        """
        connection_id = self._connection_ids.get(socket, uuid.uuid4())
        self._connection_ids[socket] = connection_id
        file_hashes = self._file_hashes.get(connection_id, dict())
        self._file_hashes[connection_id] = file_hashes
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                while True:
                    command, data = await self._decode(socket, temp_dir,
                                                       file_hashes,
                                                       connection_id)
                    # let session handle the request
                    response, files = self._handle_request(
                        command=command,
                        data=data,
                        temp_directory=temp_dir,
                        connection_id=connection_id
                    )

                    # send the response
                    logger.debug("Response: %s with %s files"
                                 % (response[:DEBUG_MAX], len(files)))
                    num_blocks, response = split_message(response)
                    await socket.send(
                        encode_header([VERSION, num_blocks, len(files)],
                                      LEN_HEADER)
                    )
                    for part in response:
                        await socket.send(part)
                    for part in encode_files(files):
                        await socket.send(part)
        except ws_exceptions.ConnectionClosedOK:
            pass
        finally:
            logger.debug("Connection %s closed!" % connection_id)
            del self._file_hashes[connection_id]
            del self._connection_ids[socket]
            self._handle_disconnect(connection_id)

    async def _decode(self,
                      socket,
                      temp_dir: str,
                      file_hashes: str,
                      connection_id: Hashable) -> Tuple[str, str, bytes]:
        """Get data from the user.

        Args:
            socket: The websocket object
            temp_dir: The place to store the files

        Raises:
            NotImplementedError: Not implemented the protocol version of
                the message. You might need to update osp-core.

        Returns:
            Tuple of command to execute, data and binary data.
        """
        bytes_data = await socket.recv()
        version, num_blocks, num_files, command = decode_header(bytes_data,
                                                                LEN_HEADER)
        if version != VERSION:
            raise NotImplementedError("No decode implemented for "
                                      "version %s" % version)
        logger.debug(
            "Received data from %s.\n\t Protocol version: %s,\n\t "
            "Command: %s,\n\t Number of files: %s."
            % (connection_id, version, command, num_files))
        data = await join_message(socket, num_blocks)
        logger.debug("Received data: %s" % data[:DEBUG_MAX])
        await receive_files(num_files, socket, temp_dir, file_hashes)
        return command, data


class CommunicationEngineClient:
    """Client side of the CommunicationEngine.

    The communication engine manages the connection between a remote and
    local side. The client will be executed on the local side.
    """

    def __init__(self,
                 uri: str,
                 handle_response: Callable,
                 **kwargs: dict[str, Any]):
        """Construct the communication engine's client.

        Args:
            uri (str): WebSocket URI.
            handle_response: Handles the responses of the server.
                Signature: str(response).
            kwargs: Will be passed to websockets.connect. E.g. it is
                possible to pass an SSL context with the ssl keyword.
        """
        self.uri = uri
        self.kwargs = kwargs
        self.handle_response = handle_response
        self.socket = None

    def send(self,
             command: str,
             data: str,
             files: Optional[Iterable[str]] = None):
        """Send a request to the server.

        Args:
            command: The command to execute on the server.
            data: The data to send to the server.
            files: List of file paths.

        Returns:
            Future: The Future’s result or raise its exception.
        """
        files = files or []
        event_loop = asyncio.get_event_loop()
        return event_loop.run_until_complete(
            self._request(command, data, files))

    def close(self) -> None:
        """Close the connection to the server."""
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self._close())

    async def _close(self):
        """Close the connection to the server."""
        if self.socket is not None:
            await self.socket.close()
            self.socket = None

    async def _request(self,
                       command: str,
                       data: str,
                       files=None) -> str:
        """Send a request to the server.

        Args:
            command: The command to execute on the server.
            data: The data to send to the server.

        Returns:
            The response for the client.
        """
        logger.debug("Request %s: %s" % (command, data[:DEBUG_MAX]))
        if self.socket is None:
            logger.debug("uri: %s" % self.uri)
            self.socket = await websockets.connect(self.uri, **self.kwargs)

        # send request to the server
        message = self._encode(command, data, files)
        for part in message:
            await self.socket.send(part)

        # load result
        with tempfile.TemporaryDirectory() as temp_dir:
            response = await self.socket.recv()
            version, num_blocks, num_files = decode_header(response,
                                                           LEN_HEADER)
            logger.debug("Response:\n\t Protocol version: %s,\n\t "
                         "Number of blocks: %s,\n\t Number of files: %s"
                         % (version, num_blocks, num_files))
            data = await join_message(self.socket, num_blocks)
            logger.debug("Response data: %s" % data[:DEBUG_MAX])
            await receive_files(num_files, self.socket, temp_dir)
            return self.handle_response(
                data=data,
                temp_directory=temp_dir
            )

    @staticmethod
    def _encode(command: str,
                data: str,
                files: List[str]) -> bytes:
        """Encode the data to send to the server to bytes.

        Args:
            command: The command to execute.
            data: The json data to send
            files: The binary data to send

        Returns:
            bytes: The resulting data encoded
        """
        files = files or []
        num_blocks, data = split_message(data)
        version = 1
        yield encode_header([version, num_blocks, len(files), command],
                            LEN_HEADER)
        yield from data
        yield from encode_files(files)
