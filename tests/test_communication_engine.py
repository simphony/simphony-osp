"""Test the communication engine."""

import unittest2 as unittest
import asyncio
import websockets
from osp.core.session.transport.communication_engine import \
    CommunicationEngineClient, CommunicationEngineServer
from osp.core.session.transport.communication_engine import LEN_HEADER
from osp.core.session.transport.communication_utils import (
    encode_header, decode_header, split_message
)


def async_test(test):
    """Test asynchronous functions with this decorator."""
    def decorate(self):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(test(self))
    return decorate


class MockWebsocket():
    """A mock websocket for testing purposes."""

    def __init__(self, id, to_recv, sent_data):
        """Initialize the MockWebsocket."""
        self.to_recv = to_recv
        self.iter = iter(to_recv)
        self.id = id
        self.sent_data = sent_data

    def reset(self):
        """Reset the iterator."""
        self.iter = iter(self.to_recv)

    def __hash__(self):
        """Make it hashable."""
        return self.id

    def __aiter__(self):
        """Mock implementation of __aiter__ magic method."""
        return self

    async def __anext__(self):
        """Mock implementation of __anext__ magic methods."""
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

    async def send(self, data):
        """Mock implementation of send methods."""
        self.sent_data.append(data)

    async def recv(self):
        """Mock implementation of recv method."""
        try:
            return next(self.iter)
        except StopIteration:
            raise websockets.exceptions.ConnectionClosedOK(code=1000,
                                                           reason=None)


class TestCommunicationEngine(unittest.TestCase):
    """Test the communication engine."""

    @async_test
    async def test_serve(self):
        """Test the serve method of the server."""
        response = []
        disconnects = []
        connection_ids = []

        def handle_request(command, data, temp_directory, connection_id):
            nonlocal connection_ids
            connection_ids.append(connection_id)
            return command + "-" + data + "!", []

        server = CommunicationEngineServer(
            host=None, port=None,
            handle_request=handle_request,
            handle_disconnect=lambda u: disconnects.append(u)
        )

        websocket = MockWebsocket(
            id=12,
            to_recv=[
                encode_header([1, 3, 0, "greet"], LEN_HEADER),
                *split_message("Hello", block_size=2)[1],
                encode_header([1, 2, 0, "say_goodbye"], LEN_HEADER),
                *split_message("Bye", block_size=2)[1]
            ],
            sent_data=response
        )

        await server._serve(websocket, None)
        version, num_blocks, num_files = decode_header(response[0], LEN_HEADER)
        self.assertEqual(version, 1)
        self.assertEqual(num_blocks, 1)
        self.assertEqual(num_files, 0)
        self.assertEqual(response[1], b"greet-Hello!")
        version, num_blocks, num_files = decode_header(response[2], LEN_HEADER)
        self.assertEqual(version, 1)
        self.assertEqual(num_blocks, 1)
        self.assertEqual(num_files, 0)
        self.assertEqual(response[3], b"say_goodbye-Bye!")
        self.assertEqual(disconnects, [connection_ids[0]])

        websocket.reset()
        await server._serve(websocket, None)
        self.assertEqual(len(connection_ids), 4)
        self.assertEqual(connection_ids[0], connection_ids[1])
        self.assertNotEqual(connection_ids[1], connection_ids[2])
        self.assertEqual(connection_ids[2], connection_ids[3])

    @async_test
    async def test_request(self):
        """Test the request method of the client."""
        responses = []
        requests = []
        client = CommunicationEngineClient(
            uri=None,
            handle_response=lambda data, temp_directory: responses.append(data)
        )
        client.websocket = MockWebsocket(
            id=7,
            to_recv=[
                encode_header([1, 3, 0], LEN_HEADER),
                *split_message("hello", block_size=2)[1],
                encode_header([1, 2, 0], LEN_HEADER),
                *split_message("bye", block_size=2)[1],
            ],
            sent_data=requests
        )
        await client._request("greet", "Hello")
        version, num_blocks, num_files, command = decode_header(requests[0],
                                                                LEN_HEADER)
        self.assertEqual(version, 1)
        self.assertEqual(num_blocks, 1)
        self.assertEqual(num_files, 0)
        self.assertEqual(command, "greet")
        self.assertEqual(requests[1], b"Hello")
        self.assertEqual(responses, ["hello"])

        await client._request("say_goodbye", "Bye")
        version, num_blocks, num_files, command = decode_header(requests[2],
                                                                LEN_HEADER)
        self.assertEqual(version, 1)
        self.assertEqual(num_blocks, 1)
        self.assertEqual(num_files, 0)
        self.assertEqual(command, "say_goodbye")
        self.assertEqual(requests[3], b"Bye")
        self.assertEqual(responses, ["hello", "bye"])


if __name__ == '__main__':
    unittest.main()
