# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import asyncio
import websockets
import logging
import os
import math
import tempfile
import hashlib
from osp.core.session.transport.transport_util import check_hash

logger = logging.getLogger(__name__)


BLOCK_SIZE = 4096


class CommunicationEngineServer():
    """The communication engine manages the connection between the remote and
    local side of the transport layer. The server will be executed on the
    remote side."""
    def __init__(self, host, port, handle_request, handle_disconnect):
        """Construct the communication engine's server.

        :param host: The hostname
        :type host: str
        :param port: The port
        :type port: int
        :param handle_request: Handles the requests of the user.
        :type handle_request: Callable[str(command), str(data), Hashable(user)]
        :param handle_disconnect: Gets called when a user disconnects.
        :type handle_disconnect: Callable[Hashable(user)]
        """
        self.host = host
        self.port = port
        self._handle_request = handle_request
        self._handle_disconnect = handle_disconnect
        self._file_hashes = dict()

    def startListening(self):
        """Start the server on given host + port."""
        event_loop = asyncio.get_event_loop()
        start_server = websockets.serve(self._serve, self.host, self.port)
        event_loop.run_until_complete(start_server)
        event_loop.run_forever()

    async def _serve(self, websocket, _):
        """Wait for requests, compute responses and serve them to the user.

        :param websocket: The websockets object.
        :type websocket: Websocket
        :param _: The path of the URI (will be ignored).
        :type _: str
        """
        file_hashes = self._file_hashes.get(websocket, dict())
        self._file_hashes[websocket] = file_hashes
        try:
            while True:
                with tempfile.TemporaryDirectory() as temp_dir:
                    command, data = await self._decode(websocket, temp_dir,
                                                       file_hashes)
                    # let session handle the request
                    response, files = self._handle_request(
                        command=command,
                        data=data,
                        temp_directory=temp_dir,
                        user=websocket
                    )

                    # send the response
                    files = _filter_files(files, file_hashes)
                    logger.debug("Response: %s with %s files"
                                 % (response, len(files)))
                    response = len(files).to_bytes(length=1, byteorder="big") \
                        + response.encode("utf-8")
                    await websocket.send(response)
                    for part in _encode_files(files):
                        await websocket.send(part)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            logger.debug("User %s disconnected!" % hash(websocket))
            del self._file_hashes[websocket]
            self._handle_disconnect(websocket)

    async def _decode(self, websocket, temp_dir, file_hashes):
        """Get data from the user.

        Args:
            websocket (websocket): The websocket object
            temp_dir (TemporaryDirectory): The place to store the files

        Raises:
            NotImplementedError: Not implemented the protocol version of
                the message. You might need to update osp-core.

        Returns:
            Tuple[str, str, bytes]: Tupole of command to execute,
                data and binary data.
        """
        bytes_data = await websocket.recv()
        version = int.from_bytes(bytes_data[0:1], byteorder="big")
        if version != 1:
            raise NotImplementedError("No decode implemented for "
                                      "version %s" % version)
        len_command = int.from_bytes(bytes_data[1:2], byteorder="big")
        num_files = int.from_bytes(bytes_data[2:3], byteorder="big")
        command = bytes_data[3: 3 + len_command].decode("utf-8")
        data = bytes_data[3 + len_command:].decode("utf-8")
        logger.debug(
            "Recieved data from %s.\n\t Protocol version: %s,\n\t "
            "Command: %s,\n\t Number of files: %s,\n\t Data: %s"
            % (hash(websocket), version, command, num_files, data))
        await _receive_files(num_files, websocket, temp_dir, file_hashes)
        return command, data


class CommunicationEngineClient():
    """The communication engine manages the connection between the remote and
    local side of the transport layer. The client will be executed on the
    local side."""

    def __init__(self, host, port, handle_response):
        """Construct the communication engine's client.

        :param host: The hostname.
        :type host: str
        :param port: The port.
        :type port: int
        :param handle_response: Handles the responses of the server.
        :type handle_response: Callable[str(response)]
        """
        self.host = host
        self.port = port
        self.handle_response = handle_response
        self.websocket = None

    def send(self, command, data, files=[]):
        """Send a request to the server

        :param command: The command to execute on the server
        :type command: str
        :param data: The data to send to the server
        :type data: str
        """
        event_loop = asyncio.get_event_loop()
        return event_loop.run_until_complete(
            self._request(command, data, files))

    def close(self):
        """Close the connection to the server"""
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self._close())

    async def _close(self):
        """Close the connection to the server."""
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None

    async def _request(self, command, data, files=None):
        """Send a request to the server.

        :param command: The command to execute on the server.
        :type command: str
        :param data: The data to send to the server.
        :type data: str
        """
        logger.debug("Request %s: %s" % (command, data))
        if self.websocket is None:
            uri = "ws://%s:%s" % (self.host, self.port)
            self.websocket = await websockets.connect(uri)

        # send request to the server
        message = self._encode(command, data, files)
        for part in message:
            await self.websocket.send(part)

        # load result
        with tempfile.TemporaryDirectory() as temp_dir:
            response = await self.websocket.recv()
            num_files = int.from_bytes(response[0:1], byteorder="big")
            data = response[1:].decode("utf-8")
            logger.debug("Response: %s with %s files" % (data, num_files))
            await _receive_files(num_files, self.websocket, temp_dir)
            return self.handle_response(
                data=data,
                temp_directory=temp_dir
            )

    def _encode(self, command, data, files):
        """Encode the data to send to the server to bytes

        Args:
            command (str): The command to execute.
            data (str): The json data to send
            binary_data (bytes): The binary data to send

        Returns:
            bytes: The resulting data encoded
        """
        files = files or []
        data = data.encode("utf-8")
        command = command.encode("utf-8")
        len_command = len(command).to_bytes(length=1, byteorder="big")
        num_files = len(files).to_bytes(length=1, byteorder="big")
        version = int(1).to_bytes(length=1, byteorder="big")
        yield version + len_command + num_files + command + data
        yield from _encode_files(files)


def _filter_files(files, file_hashes):
    """Remove the files the receiver already has

    Args:
        files (List[path]): A list of paths to send.

    Yields:
        List[str]: The files to send
    """
    result = list()
    for file in files:
        if not os.path.exists(file):
            logger.warning("Cannot send %s, because it does not exist" % file)
            continue
        if check_hash(file, file_hashes):
            logger.debug("Skip sending file %s, "
                         "receiver already has a copy of it." % file)
            continue
        result.append(file)
    return result


def _encode_files(files):
    """Encode the files to be sent to over the networks.
    Will send file in several blocks.

    Args:
        files (List[path]): A list of paths to send.

    Yields:
        bytes: The bytes of the file
    """
    logger.debug("Will send %s files" % len(files))
    for i, file in enumerate(files):
        bytes_filename = os.path.basename(file).encode("utf-8")
        num_blocks = int(math.ceil(os.path.getsize(file) / BLOCK_SIZE))
        logger.debug("Send file %s (%s of %s) with %s block(s) of %s bytes"
                     % (file, i + 1, len(files), num_blocks, BLOCK_SIZE))
        num_blocks_bytes = num_blocks.to_bytes(length=4, byteorder="big")
        yield num_blocks_bytes + bytes_filename

        # send the file contents
        with open(file, "rb") as f:
            for i, block in enumerate(iter(lambda: f.read(BLOCK_SIZE), b"")):
                logger.debug("Send block %s of %s" % (i + 1, num_blocks))
                yield block
            logger.debug("Done")


async def _receive_files(num_files, websocket, directory, file_hashes=None):
    """Will receive and store the files sent to the websocket.

    Args:
        num_files (int): The number of files to load
        websocket (websocket): The websocket to load the files from
        directory (path): The location to store the files
    """
    if file_hashes is None:
        file_hashes = dict()
    for i in range(num_files):
        logger.debug("Load file %s of %s" % (i + 1, num_files))
        description = await websocket.recv()
        num_blocks = int.from_bytes(description[0:4], byteorder="big")
        filename = description[4:].decode("utf-8")
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
