# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import sys
import time
import subprocess
import unittest2 as unittest
import sqlite3
import shutil
from osp.core.session.transport.transport_util import (
    move_files, serialize_buffers)
from osp.core.session.buffers import BufferContext
from osp.wrappers.sqlite import SqliteSession
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")

HOST = "127.0.0.1"
PORT = 8687
DB = "filetransfer.db"

FILES_DIR = os.path.join(os.path.dirname(__file__), "filetransfer_files")
CLIENT_DIR = os.path.join(os.path.dirname(__file__), "filetransfer_client")
SERVER_DIR = os.path.join(os.path.dirname(__file__), "filetransfer_server")
ENDINGS = ["", ".jpg", ".gz"]
FILES = ["f%s%s" % (i, ending) for i, ending in enumerate(ENDINGS)]
FILES[2] = "f2.tar.gz"
FILE_PATHS = [os.path.join(FILES_DIR, FILES[i]) for i in range(len(ENDINGS))]


class TestFiletransfer(unittest.TestCase):
    SERVER_STARTED = False

    @classmethod
    def setUpClass(cls):
        args = ["python3",
                "tests/test_filetransfer.py",
                "server"]
        try:
            p = subprocess.Popen(args)
        except FileNotFoundError:
            args[0] = "python"
            p = subprocess.Popen(args)

        TestFiletransfer.SERVER_STARTED = p
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        TestFiletransfer.SERVER_STARTED.terminate()
        os.remove(DB)

    def tearDown(self):
        shutil.rmtree(FILES_DIR)
        shutil.rmtree(CLIENT_DIR)
        shutil.rmtree(SERVER_DIR)
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            tables = c.execute("SELECT name FROM sqlite_master "
                               + "WHERE type='table';")
            tables = list(tables)
            for table in tables:
                c.execute("DELETE FROM %s;" % table[0])
            conn.commit()

    def setUp(self):
        if not os.path.exists(FILES_DIR):
            os.mkdir(FILES_DIR)
        if not os.path.exists(CLIENT_DIR):
            os.mkdir(CLIENT_DIR)
        if not os.path.exists(SERVER_DIR):
            os.mkdir(SERVER_DIR)
        open(FILE_PATHS[0], "w").close()
        open(FILE_PATHS[1], "w").close()
        open(FILE_PATHS[2], "w").close()

    def test_move_files(self):
        with TransportSessionClient(SqliteSession, HOST, PORT) as session:
            # Image path is full path
            wrapper = CITY.CITY_WRAPPER(session=session)
            images = wrapper.add(
                CITY.IMAGE(path=FILE_PATHS[0]),
                CITY.IMAGE(path=FILE_PATHS[1]),
                CITY.IMAGE(path=FILE_PATHS[2])
            )
            result = move_files(images, None, CLIENT_DIR)
            target = ["%s%s" % (image.uid, ending)
                      for image, ending in zip(images, ENDINGS)]
            target_full_path = [os.path.join(CLIENT_DIR, t) for t in target]

            self.assertEqual(set(os.listdir(FILES_DIR)), set(FILES))
            self.assertEqual(set(os.listdir(CLIENT_DIR)), set(target))
            self.assertEqual(result, target_full_path)

            self.tearDown()
            self.setUp()

            # Image path is path on a different system
            paths = [FILES[0], os.path.join("foo", "bar", FILES[1]),
                     os.path.abspath('.').split(os.path.sep)[0]
                     + os.path.sep + FILES[2]]
            images = wrapper.add(
                CITY.IMAGE(path=paths[0]),
                CITY.IMAGE(path=paths[1]),
                CITY.IMAGE(path=paths[2])
            )
            result = move_files(images, FILES_DIR, CLIENT_DIR)
            target = ["%s%s" % (image.uid, ending)
                      for image, ending in zip(images, ENDINGS)]
            target_full_path = [os.path.join(CLIENT_DIR, t) for t in target]
            self.assertEqual(set(os.listdir(CLIENT_DIR)), set(target))
            self.assertEqual(result, target_full_path)

            self.tearDown()
            self.setUp()

            # Not target given --> Nothing will be moved
            images = wrapper.add(
                CITY.IMAGE(path=paths[0]),
                CITY.IMAGE(path=paths[1]),
                CITY.IMAGE(path=paths[2])
            )
            result = move_files(images, FILES_DIR, None)
            self.assertEqual(set(os.listdir(CLIENT_DIR)), set())
            self.assertEqual(result, paths)

            # Target does not exist
            images = wrapper.add(
                CITY.IMAGE(path=paths[0]),
                CITY.IMAGE(path=paths[1]),
                CITY.IMAGE(path=paths[2])
            )
            result = move_files(images, FILES_DIR, "not-existent")
            self.assertEqual(set(os.listdir(CLIENT_DIR)), set())
            self.assertEqual(result, list())

            # paths don't exist
            images = wrapper.add(
                CITY.IMAGE(path=paths[0]),
                CITY.IMAGE(path=paths[1]),
                CITY.IMAGE(path=paths[2])
            )
            result = move_files(images, None, CLIENT_DIR)
            self.assertEqual(set(os.listdir(CLIENT_DIR)), set())
            self.assertEqual(result, list())

    def serialize_buffers(self):
        with TransportSessionClient(SqliteSession, HOST, PORT) as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            images = wrapper.add(
                CITY.IMAGE(path=FILE_PATHS[0]),
                CITY.IMAGE(path=FILE_PATHS[1])
            )
            session._reset_buffers(BufferContext.USER)
            wrapper.remove(images[1].uid)
            images += wrapper.add(CITY.IMAGE(path=FILE_PATHS[2]))
            session.prune()
            _, result = serialize_buffers(
                session, buffer_context=BufferContext.USER,
                target_directory=None)
            self.assertEqual(
                [],
                result
            )
            # added, updated, deleted = s1._buffers[BufferContext.USER]
            # self.assertEqual(added.keys(), {uuid.UUID(int=2)})
            # self.assertEqual(updated.keys(), {uuid.UUID(int=0)})
            # self.assertEqual(deleted.keys(), {uuid.UUID(int=1)})
            # self.assertEqual(s1._buffers[BufferContext.ENGINE],
            #                  [dict(), dict(), dict()])
            # self.maxDiff = None
            # self.assertEqual(
            #     (SERIALIZED_BUFFERS, []),
            #     serialize_buffers(
            #         s1, buffer_context=BufferContext.USER,
            #         additional_items={
            #             "args": [42], "kwargs": {"name": "London"}
            #         }
            #     )
            # )
            # self.assertEqual(s1._buffers, [
            #     [dict(), dict(), dict()],
            #     [dict(), dict(), dict()]
            # ])
            # s1._expired = {uuid.UUID(int=0), uuid.UUID(int=2)}


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        server = TransportSessionServer(SqliteSession, HOST, PORT,
                                        session_kwargs={"path": DB})
        server.startListening()
