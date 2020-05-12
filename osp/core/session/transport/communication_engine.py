# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import asyncio
import websockets
import logging
import tempfile
from osp.core.session.transport.communication_utils import (
    decode_header, encode_header, split_message, join_message, filter_files,
    encode_files, receive_files
)

logger = logging.getLogger(__name__)


LEN_HEADER = [2, 5, 2]  # version, num_blocks, num_files
VERSION = 1
DEBUG_MAX = 1000


class CommunicationEngineServer():
    """The communication engine manages the connection between the remote and
    local side of the transport layer. The server will be executed on the
    remote side."""

    def __init__(self, host, port, handle_request, handle_disconnect):
        """Construct the communication engine's server.

        Args:
            host (str): The hostname.
            port (int): The port.
            handle_request (Callable[str(command), str(data), Hashable(user)]):
            Handles the requests of the user.
            handle_disconnect (Callable[Hashable(user)]): Gets called when a
                user disconnects.
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
        """Waits for requests, compute responses and serve them to the user.

        Args:
            websocket (Websocket): The websockets object.
            _ (str): The path of the URI (will be ignored).
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
                    files = filter_files(files, file_hashes)
                    logger.debug("Response: %s with %s files"
                                 % (response[:DEBUG_MAX], len(files)))
                    response = response.encode("utf-8")
                    num_blocks, response = split_message(response)
                    await websocket.send(
                        encode_header([VERSION, num_blocks, len(files)],
                                      LEN_HEADER)
                    )
                    for part in response:
                        await websocket.send(part)
                    for part in encode_files(files):
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
        version, num_blocks, num_files, command = decode_header(bytes_data,
                                                                LEN_HEADER)
        if version != VERSION:
            raise NotImplementedError("No decode implemented for "
                                      "version %s" % version)
        logger.debug(
            "Received data from %s.\n\t Protocol version: %s,\n\t "
            "Command: %s,\n\t Number of files: %s."
            % (hash(websocket), version, command, num_files))
        data = await join_message(websocket, num_blocks)
        logger.debug("Received data: %s" % data[:DEBUG_MAX])
        await receive_files(num_files, websocket, temp_dir, file_hashes)
        return command, data


class CommunicationEngineClient():
    """The communication engine manages the connection between the remote and
    local side of the transport layer. The client will be executed on the
    local side."""

    def __init__(self, uri, handle_response):
        """Constructs the communication engine's client.

        Args:
            uri (str): WebSocket URI.
            handle_response (Callable[str(response)]): Handles the responses of
                the server.
        """
        self.uri = uri
        self.handle_response = handle_response
        self.websocket = None

    def send(self, command, data, files=[]):
        """Sends a request to the server.

        Args:
            command (str): The command to execute on the server.
            data (str): The data to send to the server.

        Returns:
            Future: The Future’s result or raise its exception.
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

        Args:
            command (str): The command to execute on the server.
            data (str): The data to send to the server.

        Returns:
            str: The response for the client.
        """
        logger.debug("Request %s: %s" % (command, data[:DEBUG_MAX]))
        if self.websocket is None:
            logger.debug("uri: %s" % (self.uri))
            self.websocket = await websockets.connect(self.uri)

        # send request to the server
        message = self._encode(command, data, files)
        for part in message:
            await self.websocket.send(part)

        # load result
        with tempfile.TemporaryDirectory() as temp_dir:
            response = await self.websocket.recv()
            version, num_blocks, num_files = decode_header(response,
                                                           LEN_HEADER)
            logger.debug("Response:\n\t Protocol version: %s,\n\t "
                         "Number of blocks: %s,\n\t Number of files: %s"
                         % (version, num_blocks, num_files))
            data = await join_message(self.websocket, num_blocks)
            logger.debug("Response data: %s" % data[:DEBUG_MAX])
            await receive_files(num_files, self.websocket, temp_dir)
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
        num_blocks, data = split_message(data)
        version = 1
        yield encode_header([version, num_blocks, len(files), command],
                            LEN_HEADER)
        yield from data
        yield from encode_files(files)
