# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import asyncio
import websockets
import logging

logger = logging.getLogger(__name__)


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
        try:
            async for data in websocket:
                command = data.split(":")[0]
                data = data[len(command) + 1:]
                logger.debug("Request %s: %s from %s",
                             command, data, hash(websocket))
                response = self._handle_request(command, data, websocket)
                logger.debug("Response: %s" % response)
                await websocket.send(response)
        finally:
            logger.debug("User %s disconnected!" % hash(websocket))
            self._handle_disconnect(websocket)


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

    def send(self, command, data):
        """Sends a request to the server.

        Args:
            command (str): The command to execute on the server.
            data (str): The data to send to the server.

        Returns:
            Future: The Future’s result or raise its exception.
        """
        event_loop = asyncio.get_event_loop()
        return event_loop.run_until_complete(self._request(command, data))

    def close(self):
        """Close the connection to the server"""
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self._close())

    async def _close(self):
        """Close the connection to the server."""
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None

    async def _request(self, command, data):
        """Send a request to the server.

        Args:
            command (str): The command to execute on the server.
            data (str): The data to send to the server.

        Returns:
            str: The response for the client.
        """        
        logger.debug("Request %s: %s" % (command, data))
        if self.websocket is None:
            logger.debug("uri: %s" % (self.uri))
            self.websocket = await websockets.connect(self.uri)
        await self.websocket.send(command + ":" + data)
        response = await self.websocket.recv()
        logger.debug("Response: %s" % response)
        return self.handle_response(response)
