"""Utilities used in the communication for the remote stores."""

import asyncio
import logging
import math
import os
import tempfile
import uuid
from itertools import chain
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)
from uuid import UUID

import websockets
import websockets.exceptions as ws_exceptions
from websockets.legacy.client import WebSocketClientProtocol as Socket
from websockets.legacy.server import WebSocketServerProtocol as ServerSocket

from simphony_osp.interfaces.remote.common import COMMAND

logger = logging.getLogger(__name__)

BLOCK_SIZE = 4096
LEN_FILES_HEADER = [5]  # num_blocks
LEN_HEADER = [2, 5, 2]  # version, num_blocks, num_files
VERSION = 2
DEBUG_MAX = 1000


def clear_directory(directory: str) -> None:
    """Remove all the files and subdirectories contained within a folder."""
    for path, directory_names, file_names in os.walk(directory):
        for element in chain(file_names, directory_names):
            os.unlink(os.path.join(path, element))


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
        yield int.from_bytes(bytestring[i : i + length], byteorder="big")
        i += length
    if len(bytestring) > i:
        yield bytestring[i:].decode("utf-8")


def encode_header(
    elements: List[Union[int, str]], lengths: List[int]
) -> bytes:
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

    def gen(message, blocks, size):
        for i in range(blocks):
            logger.debug(f"Sending message block {i + 1} of {blocks}")
            yield message[i * size : (i + 1) * size]
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
        logger.debug(f"Receiving message block {i + 1} of {num_blocks}")
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
        logger.debug(
            "Send file %s (%s of %s) with %s block(s) of %s bytes"
            % (file, i + 1, len(files), num_blocks, BLOCK_SIZE)
        )
        yield encode_header([num_blocks, filename], LEN_FILES_HEADER)

        # send the file contents
        with open(file, "rb") as f:
            for i, block in enumerate(iter(lambda: f.read(BLOCK_SIZE), b"")):
                logger.debug(f"Send file block {i + 1} of {num_blocks}")
                yield block
            logger.debug("Done")


async def receive_files(
    num_files: int, websocket: Union[Socket, ServerSocket]
) -> List[BinaryIO]:
    """Will receive and store the files sent to the websocket.

    Args:
        num_files: The number of files to load.
        websocket: The websocket to load the files from.
    """
    files = []
    for i in range(num_files):
        logger.debug(f"Load file {i + 1} of {num_files}")
        num_blocks, filename = decode_header(
            await websocket.recv(), LEN_FILES_HEADER
        )
        file = tempfile.NamedTemporaryFile(delete=False)
        files.append(file)
        logger.debug("Storing file %s with %s blocks." % file.name)
        with file:
            for j in range(num_blocks):
                logger.debug(f"Receive block {j + 1} of {num_blocks}")
                data = await websocket.recv()
                file.write(data)
        file.seek(0)
    return files


class CommunicationEngineServer:
    """Server side of the CommunicationEngine.

    The communication engine manages the connection between the remote and
    a local side. The server will be executed on the remote side.
    """

    host: str
    port: int
    credentials: Dict[UUID, Tuple[str, str]]

    def __init__(
        self,
        host: str,
        port: int,
        handle_request: Callable[
            [COMMAND, str, List[BinaryIO], UUID], Tuple[str, List[str]]
        ],
        handle_disconnect: Callable[[UUID], None],
    ) -> None:
        """Construct the communication engine's server.

        Args:
            host: The hostname.
            port: The port.
            handle_request: Handles the requests of the user.
            handle_disconnect: Gets called when a user disconnects.
        """
        self.host = host
        self.port = port
        self._handle_request = handle_request
        self._handle_disconnect = handle_disconnect
        self._connections = dict()
        self.credentials = dict()

    def listen(self) -> None:
        """Start the server on given host and port."""
        event_loop = asyncio.get_event_loop()
        start_server = websockets.serve(self._serve, self.host, self.port)
        event_loop.run_until_complete(start_server)
        event_loop.run_forever()

    async def _serve(self, socket: ServerSocket, _: str) -> None:
        """Wait for requests, compute responses and serve them to the user.

        Args:
            socket: The websockets object.
        """
        self._connections[socket] = self._connections.get(socket, uuid.uuid4())
        connection = self._connections[socket]

        try:
            while True:
                # receive the request
                command, data, files = await self._decode(socket)
                command = COMMAND(command)  # Validate command
                # handle the request and produce a response
                response, response_files = self._handle_request(
                    command, data, files, connection
                )
                # clean-up received files
                for file in files:
                    file.close()
                    os.remove(file.name)
                # send the response
                logger.debug(
                    "Response: %s with %s files"
                    % (response[:DEBUG_MAX], len(response_files))
                )
                num_blocks, response = split_message(response)
                await socket.send(
                    encode_header(
                        [VERSION, num_blocks, len(response_files)], LEN_HEADER
                    )
                )
                for part in response:
                    await socket.send(part)
                # send response files
                if len(response_files) > 0:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_names = []
                        for i, file in enumerate(response_files):
                            file_name = os.path.join(temp_dir.name, str(i))
                            with open("wb", file_name) as tmp_file:
                                tmp_file.write(file)
                            file_names.append(file_name)
                        for part in encode_files(file_names):
                            await socket.send(part)
        except ws_exceptions.ConnectionClosedOK:
            pass
        finally:
            logger.debug("Connection %s closed!" % connection)
            del self._connections[socket]
            self._handle_disconnect(connection)

    async def _decode(
        self, socket: ServerSocket
    ) -> Tuple[str, str, List[BinaryIO]]:
        """Get data from the user.

        Args:
            socket: The websocket object

        Raises:
            NotImplementedError: Not implemented the protocol version of
                the message. You might need to update SimPhoNy.

        Returns:
            Tuple of command to execute and data
        """
        connection = self._connections[socket]

        bytes_data = await socket.recv()
        version, num_blocks, num_files, command = decode_header(
            bytes_data, LEN_HEADER
        )
        if version != VERSION:
            raise NotImplementedError(
                "No decode implemented for " "version %s" % version
            )
        logger.debug(
            "Received data from %s.\n\t Protocol version: %s,\n\t "
            "Command: %s,\n\t Number of files: %s."
            % (connection, version, command, num_files)
        )
        data = await join_message(socket, num_blocks)
        logger.debug("Received data: %s" % data[:DEBUG_MAX])
        files = await receive_files(num_files, socket)
        return command, data, files


class CommunicationEngineClient:
    """Client side of the CommunicationEngine.

    The communication engine manages the connection between a remote and
    local side. The client will be executed on the local side.
    """

    socket: Optional[Socket] = None

    def __init__(self, uri: str, handle_response: Callable[..., Any]):
        """Construct the communication engine's client.

        Args:
            uri: WebSocket URI.
            handle_response: Handles the responses of the server.
                Signature: str(response).
        """
        self.uri = uri
        self._handle_response = handle_response

    def send(
        self,
        command: COMMAND,
        data: str,
        files: Optional[Iterable[str]] = None,
    ):
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
            self._request(command, data, files)
        )

    def close(self) -> None:
        """Close the connection to the server."""
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self._close())

    async def _request(
        self, command: COMMAND, data: str, files: List[str]
    ) -> str:
        """Send a request to the server.

        Args:
            command: The command to execute on the server.
            data: The data to send to the server.

        Returns:
            The response for the client.
        """
        logger.debug(f"Request {command}: {data[:DEBUG_MAX]}")
        if self.socket is None:
            logger.debug("uri: %s" % self.uri)
            self.socket = await websockets.connect(self.uri)

        # send request to the server
        message = self._encode(command, data, files)
        for part in message:
            await self.socket.send(part)

        # handle response
        response = await self.socket.recv()
        version, num_blocks, num_files = decode_header(response, LEN_HEADER)
        logger.debug(
            "Response:\n\t Protocol version: %s,\n\t "
            "Number of blocks: %s,\n\t Number of files: %s"
            % (version, num_blocks, num_files)
        )
        data = await join_message(self.socket, num_blocks)
        logger.debug("Response data: %s" % data[:DEBUG_MAX])
        files = await receive_files(num_files, self.socket)
        return self._handle_response(data=data, files=files)

    async def _close(self):
        """Close the connection to the server."""
        if self.socket is not None:
            await self.socket.close()
            self.socket = None

    def __del__(self):
        """Close the connection on garbage collection."""
        self.close()

    @staticmethod
    def _encode(command: COMMAND, data: str, files: List[str]) -> bytes:
        """Encode the data to send to the server to bytes.

        Args:
            command: The command to execute.
            data: The json data to send.
            files: The binary data to send.

        Returns:
            bytes: The resulting data encoded
        """
        files = files
        num_blocks, data = split_message(data)
        version = VERSION
        yield encode_header(
            [version, num_blocks, len(files), command], LEN_HEADER
        )
        yield from data
        yield from encode_files(files)
