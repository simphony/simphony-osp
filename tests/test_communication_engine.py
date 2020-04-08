# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import asyncio
from osp.core.session.transport.communication_engine import \
    CommunicationEngineClient, CommunicationEngineServer


HELLO_MSG = bytes([1, 5, 0, 0, 0, 0, 0, 0, 0, 5]) \
    + "greetHello".encode("utf-8")
GOODBYE_MSG = bytes([1, 11, 0, 0, 0, 0, 0, 0, 0, 3]) + \
    "say_goodbyeBye".encode("utf-8")


def async_test(test):
    def decorate(self):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(test(self))
    return decorate


class MockWebsocket():
    def __init__(self, id, to_recv, sent_data):
        self.iter = iter(to_recv)
        self.id = id
        self.sent_data = sent_data

    def __hash__(self):
        return self.id

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

    async def send(self, data):
        self.sent_data.append(data)

    async def recv(self):
        return next(self.iter)


class TestCommunicationEngine(unittest.TestCase):

    def setUp(self):
        pass

    @async_test
    async def test_serve(self):
        """Test the serve method of the server"""
        responses = []
        disconnects = []
        server = CommunicationEngineServer(
            host=None, port=None,
            handle_request=(
                lambda command, data, files_directory, user:
                    (command + "-" + data + "!", [])),
            handle_disconnect=lambda u: disconnects.append(u)
        )
        websocket = MockWebsocket(
            id=12,
            to_recv=[HELLO_MSG, GOODBYE_MSG],
            sent_data=responses
        )
        await server._serve(websocket, None)
        self.assertEqual(responses, ["greet-Hello!", "say_goodbye-Bye!"])
        self.assertEqual(disconnects, [websocket])

    @async_test
    async def test_request(self):
        """Test the request method of the client"""
        responses = []
        requests = []
        client = CommunicationEngineClient(
            host=None, port=None,
            handle_response=lambda x: responses.append(x)
        )
        client.websocket = MockWebsocket(
            id=7,
            to_recv=["hello", "bye"],
            sent_data=requests
        )
        await client._request("greet", "Hello")
        self.assertEqual(requests, [HELLO_MSG])
        self.assertEqual(responses, ["hello"])

        await client._request("say_goodbye", "Bye")
        self.assertEqual(requests, [HELLO_MSG, GOODBYE_MSG])
        self.assertEqual(responses, ["hello", "bye"])


if __name__ == '__main__':
    unittest.main()
