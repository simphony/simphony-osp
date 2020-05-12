# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
from osp.core.session.transport.communication_utils import (
    decode_header, encode_header, split_message, join_message)
from test_communication_engine import async_test, MockWebsocket


class TestFiletransfer(unittest.TestCase):
    def test_decode_header(self):
        """Test decoding of the header"""
        self.assertEqual(list(decode_header(bytes([255, 255, 0]), [2, 1])),
                         [65535, 0])
        self.assertEqual(list(decode_header(bytes([42, 24]) + b"abc", [1, 1])),
                         [42, 24, "abc"])
        self.assertRaises(IndexError, list,
                          decode_header(bytes([255]), [2]))

    def test_encode_header(self):
        """Test encoding of headers"""
        self.assertEqual(encode_header([65535, 24, "abc"], [2, 2]),
                         bytes([255, 255, 0, 24]) + b"abc")
        self.assertEqual(encode_header([65535, 24], [2, 2]),
                         bytes([255, 255, 0, 24]))
        self.assertRaises(NotImplementedError, encode_header,
                          ["abc", 65535, 24], [2, 2])
        self.assertRaises(NotImplementedError, encode_header,
                          [22, 65535, 24], [2, 2])
        self.assertRaises(ValueError, encode_header,
                          [22, 65535, 24, 22], [2, 2])

    def test_split_message(self):
        """Test splitting messages"""
        num_blocks, gen = split_message("abcdefgh", 2)
        self.assertEqual(num_blocks, 4)
        self.assertEqual(list(gen), [b"ab", b"cd", b"ef", b"gh"])
        num_blocks, gen = split_message("abcdefgh", 3)
        self.assertEqual(num_blocks, 3)
        self.assertEqual(list(gen), [b"abc", b"def", b"gh"])

    @async_test
    async def test_join_messages(self):
        """Test joining messages"""
        ws = MockWebsocket(0, to_recv=[b"ab", b"cd", b"ef", b"gh"],
                           sent_data=[])
        self.assertEqual(await join_message(websocket=ws, num_blocks=4),
                         "abcdefgh")
        ws = MockWebsocket(0, to_recv=[b"abc", b"def", b"gh"],
                           sent_data=[])
        self.assertEqual(await join_message(websocket=ws, num_blocks=3),
                         "abcdefgh")
        ws = MockWebsocket(0, to_recv=[b"ab", b"cd", b"ef", b"gh"],
                           sent_data=[])
        self.assertEqual(await join_message(websocket=ws, num_blocks=3),
                         "abcdef")
        ws = MockWebsocket(0, to_recv=[b"ab", b"cd", b"ef", b"gh"],
                           sent_data=[])


if __name__ == "__main__":
    unittest.main()
