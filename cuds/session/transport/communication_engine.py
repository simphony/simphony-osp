# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import asyncio
import websockets


class CommunicationEngineServer():
    """The communication engine manages the connection between the remote and
    local side of the transport layer. The server will be executed on the
    remote side."""
    def __init__(self, host, port, handle_request, handle_disconnect, verbose):
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
        self.verbose = verbose

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
            async for data in websocket:
                command = data.split(":")[0]
                data = data[len(command) + 1:]
                if self.verbose:
                    print("Request %s: %s from %s" %
                          (command, data, hash(websocket)))
                response = self._handle_request(command, data, websocket)
                if self.verbose:
                    print("Response: %s" % response)
                await websocket.send(response)
        finally:
            if self.verbose:
                print("User %s disconnected!" % hash(websocket))
            self._handle_disconnect(websocket)


class CommunicationEngineClient():
    """The communication engine manages the connection between the remote and
    local side of the transport layer. The client will be executed on the
    local side."""

    def __init__(self, host, port, handle_response, verbose):
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
        self.verbose = verbose

    def send(self, command, data):
        """Send a request to the server

        :param command: The command to execute on the server
        :type command: str
        :param data: The data to send to the server
        :type data: str
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

        :param command: The command to execute on the server.
        :type command: str
        :param data: The data to send to the server.
        :type data: str
        """
        if self.verbose:
            print("Request %s: %s" % (command, data))
        if self.websocket is None:
            uri = "ws://%s:%s" % (self.host, self.port)
            self.websocket = await websockets.connect(uri)
        await self.websocket.send(command + ":" + data)
        response = await self.websocket.recv()
        if self.verbose:
            print("Response: %s" % response)
        return self.handle_response(response)
