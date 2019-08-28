# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import asyncio
import websockets


class CommunicationEngineServer():
    def __init__(self, host, port, handle_request):
        self.host = host
        self.port = port
        self.handle_request = handle_request

    def startListening(self):
        event_loop = asyncio.get_event_loop()
        start_server = websockets.serve(self._serve, self.host, self.port)
        event_loop.run_until_complete(start_server)
        event_loop.run_forever()

    async def _serve(self, websocket, path):
        data = await websocket.recv()
        print("Request %s: %s" % (path, data))
        response = self.handle_request(path[1:], data)
        print("Response: %s" % response)
        await websocket.send(response)


class CommunicationEngineClient():
    def __init__(self, host, port, handle_response):
        self.host = host
        self.port = port
        self.handle_response = handle_response

    def send(self, path, data):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self._request(path, data))

    async def _request(self, path, data):
        print("Request %s: %s" % (path, data))
        uri = "ws://%s:%s/%s" % (self.host, self.port, path)
        async with websockets.connect(uri) as websocket:
            await websocket.send(data)
            response = await websocket.recv()
            print("Response: %s" % response)
            self.handle_response(response)
