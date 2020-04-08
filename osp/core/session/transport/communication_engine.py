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
import tempfile

logger = logging.getLogger(__name__)


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
        try:
            async for bytes_data in websocket:
                with tempfile.TemporaryDirectory() as files_directory:
                    command, data = self._decode(bytes_data, files_directory)
                    logger.debug("Request %s: %s from %s",
                                 command, data, hash(websocket))
                    response, files = self._handle_request(
                        command=command,
                        data=data,
                        files_directory=files_directory,
                        user=websocket
                    )   # TODO send files also
                    logger.debug("Response: %s" % response)
                    await websocket.send(response)
        finally:
            logger.debug("User %s disconnected!" % hash(websocket))
            self._handle_disconnect(websocket)

    def _decode(self, bytes_data, files_directory):
        """Decode the bytes data from the user.

        Args:
            bytes_data (bytes): The bytes sent by the user

        Raises:
            NotImplementedError: Not implemented the protocol version of
                the message. You might need to update osp-core.

        Returns:
            Tuple[str, str, bytes]: Tupole of command to execute,
                data and binary data.
        """
        version = int.from_bytes(bytes_data[0:1], byteorder="big")
        if version != 1:
            raise NotImplementedError("No decode implemented for "
                                      "version %s" % version)
        len_command = int.from_bytes(bytes_data[1:2], byteorder="big")
        len_data = int.from_bytes(bytes_data[2:10], byteorder="big")
        command = bytes_data[10: 10 + len_command].decode("utf-8")
        data = bytes_data[10 + len_command: 10 + len_command + len_data] \
            .decode("utf-8")
        _decode_files(bytes_data[10 + len_command + len_data:],
                      files_directory)
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

        message = self._encode(command, data, files)
        await self.websocket.send(message)
        response = await self.websocket.recv()
        logger.debug("Response: %s" % response)
        return self.handle_response(response)

    def _encode(self, command, data, files):
        """Encode the data to send to the server to bytes

        Args:
            command (str): The command to execute.
            data (str): The json data to send
            binary_data (bytes): The binary data to send

        Returns:
            bytes: The resulting data encoded
        """
        data = data.encode("utf-8")
        command = command.encode("utf-8")
        len_data = len(data).to_bytes(length=8, byteorder="big")
        len_command = len(command).to_bytes(length=1, byteorder="big")
        version = int(1).to_bytes(length=1, byteorder="big")
        message = version + len_command + len_data + command + data
        if files:
            message += _encode_files(files)
        return message


def _encode_files(files):
    result = bytes([])
    for file in files:
        with open(file, "rb") as f:
            bytes_data = f.read()
            bytes_filename = file.encode("utf-8")
            len_data = len(bytes_data).to_bytes(length=8, byteorder="big")
            len_name = len(bytes_filename).to_bytes(length=2, byteorder="big")
            result += len_name + len_data + bytes_filename + bytes_data
            logger.info("Will upload %s" % file)
    return result


def _decode_files(bytes_data, directory):
    while bytes_data:
        len_name = int.from_bytes(bytes_data[0:2], byteorder="big")
        len_data = int.from_bytes(bytes_data[2:10], byteorder="big")
        name = bytes_data[10: 10 + len_name].decode("utf-8")
        content = bytes_data[10 + len_name: 10 + len_name + len_data]
        name = os.path.basename(name)
        file_path = os.path.join(directory, name)
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info("Uploaded file %s and stored at %s" % (name, file_path))
        bytes_data = bytes_data[10 + len_name + len_data:]
