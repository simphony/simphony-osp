"""Server side of the CommunicationEngine.

The communication engine manages the connection between the remote and
local side of the transport layer. The server will be executed on the
remote side.
"""

import asyncio
import logging
import tempfile
import uuid

import websockets
import websockets.exceptions as ws_exceptions

from osp.core.session.transport.communication_utils import (
    decode_header,
    encode_files,
    encode_header,
    filter_files,
    join_message,
    receive_files,
    split_message,
)

logger = logging.getLogger(__name__)


LEN_HEADER = [2, 5, 2]  # version, num_blocks, num_files
VERSION = 1
DEBUG_MAX = 1000


class CommunicationEngineServer:
    """Server side of the CommunicationEngine.

    The communication engine manages the connection between the remote and
    local side of the transport layer. The server will be executed on the
    remote side.
    """

    def __init__(
        self, host, port, handle_request, handle_disconnect, **kwargs
    ):
        """Construct the communication engine's server.

        Args:
            host (str): The hostname.
            port (int): The port.
            handle_request (Callable): Handles the requests of the user.
                Signature: command(str), data(str), temp_directory(str),
                    user(UUID).
            handle_disconnect (Callable[UUID(user)]): Gets called when a
                user disconnects.
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

    def startListening(self):
        """Start the server on given host + port."""
        event_loop = asyncio.get_event_loop()
        start_server = websockets.serve(
            self._serve, self.host, self.port, **self.kwargs
        )
        event_loop.run_until_complete(start_server)
        event_loop.run_forever()

    async def _serve(self, websocket, _):
        """Wait for requests, compute responses and serve them to the user.

        Args:
            websocket (Websocket): The websockets object.
            _ (str): The path of the URI (will be ignored).
        """
        connection_id = self._connection_ids.get(websocket, uuid.uuid4())
        self._connection_ids[websocket] = connection_id
        file_hashes = self._file_hashes.get(connection_id, dict())
        self._file_hashes[connection_id] = file_hashes
        try:
            while True:
                with tempfile.TemporaryDirectory() as temp_dir:
                    command, data = await self._decode(
                        websocket, temp_dir, file_hashes, connection_id
                    )
                    # let session handle the request
                    response, files = self._handle_request(
                        command=command,
                        data=data,
                        temp_directory=temp_dir,
                        connection_id=connection_id,
                    )

                    # send the response
                    files = filter_files(files, file_hashes)
                    logger.debug(
                        "Response: %s with %s files"
                        % (response[:DEBUG_MAX], len(files))
                    )
                    num_blocks, response = split_message(response)
                    await websocket.send(
                        encode_header(
                            [VERSION, num_blocks, len(files)], LEN_HEADER
                        )
                    )
                    for part in response:
                        await websocket.send(part)
                    for part in encode_files(files):
                        await websocket.send(part)
        except ws_exceptions.ConnectionClosedOK:
            pass
        finally:
            logger.debug("Connection %s closed!" % connection_id)
            del self._file_hashes[connection_id]
            del self._connection_ids[websocket]
            self._handle_disconnect(connection_id)

    async def _decode(self, websocket, temp_dir, file_hashes, connection_id):
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
            % (connection_id, version, command, num_files)
        )
        data = await join_message(websocket, num_blocks)
        logger.debug("Received data: %s" % data[:DEBUG_MAX])
        await receive_files(num_files, websocket, temp_dir, file_hashes)
        return command, data


class CommunicationEngineClient:
    """Client side of the CommunicationEngine.

    The communication engine manages the connection between the remote and
    local side of the transport layer. The client will be executed on the
    local side.
    """

    def __init__(self, uri, handle_response, **kwargs):
        """Construct the communication engine's client.

        Args:
            uri (str): WebSocket URI.
            handle_response (Callable[str(response)]): Handles the responses of
                the server.
            kwargs (dict[str, Any]): Will be passed to websockets.connect.
                E.g. it is possible to pass an SSL context with the ssl
                keyword.
        """
        self.uri = uri
        self.kwargs = kwargs
        # The default `ping_timeout` is 20s. The pings are not sent during a
        # transfer. Thus, if the transfer takes more than 20s, then the
        # default value causes the websockets connection to close
        # unexpectedly. Hence, we chose to never close the connection due to
        # ping timeouts unless the user wishes to do so.
        self.kwargs["ping_timeout"] = self.kwargs.get("ping_timeout", None)
        self.handle_response = handle_response
        self.websocket = None

    def send(self, command, data, files=[]):
        """Send a request to the server.

        Args:
            command (str): The command to execute on the server.
            data (str): The data to send to the server.

        Returns:
            Future: The Future’s result or raise its exception.
        """
        event_loop = asyncio.get_event_loop()
        return event_loop.run_until_complete(
            self._request(command, data, files)
        )

    def close(self):
        """Close the connection to the server."""
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
            self.websocket = await websockets.connect(self.uri, **self.kwargs)

        # send request to the server
        message = self._encode(command, data, files)
        for part in message:
            await self.websocket.send(part)

        # load result
        with tempfile.TemporaryDirectory() as temp_dir:
            response = await self.websocket.recv()
            version, num_blocks, num_files = decode_header(
                response, LEN_HEADER
            )
            logger.debug(
                "Response:\n\t Protocol version: %s,\n\t "
                "Number of blocks: %s,\n\t Number of files: %s"
                % (version, num_blocks, num_files)
            )
            data = await join_message(self.websocket, num_blocks)
            logger.debug("Response data: %s" % data[:DEBUG_MAX])
            await receive_files(num_files, self.websocket, temp_dir)
            return self.handle_response(data=data, temp_directory=temp_dir)

    def _encode(self, command, data, files):
        """Encode the data to send to the server to bytes.

        Args:
            command (str): The command to execute.
            data (str): The json data to send
            binary_data (bytes): The binary data to send

        Returns:
            bytes: The resulting data encoded
        """
        files = files or []
        num_blocks, data = split_message(data)
        version = 1
        yield encode_header(
            [version, num_blocks, len(files), command], LEN_HEADER
        )
        yield from data
        yield from encode_files(files)
