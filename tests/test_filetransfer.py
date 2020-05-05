# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import sys
import time
import uuid
import subprocess
import unittest2 as unittest
import sqlite3
import shutil
from osp.core.session.transport.transport_util import (
    move_files, serialize_buffers, deserialize_buffers, get_file_cuds)
from osp.core.session.transport.communication_engine import (
    _encode_files, _receive_files
)
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


SERIALIZED_BUFFERS = (
    '{"added": [{"oclass": "CITY.IMAGE", "uid": "00000000-0000-0000-0000-000000000003", '
    '"attributes": {"path": "%s"}, '
    '"relationships": {"CITY.IS_PART_OF": {"00000000-0000-0000-0000-00000000002a": "CITY.CITY_WRAPPER"}}}], '
    '"updated": [{"oclass": "CITY.CITY_WRAPPER", "uid": "00000000-0000-0000-0000-00000000002a", '
    '"attributes": {}, '
    '"relationships": {"CITY.HAS_PART": {"00000000-0000-0000-0000-000000000001": "CITY.IMAGE", "00000000-0000-0000-0000-000000000003": "CITY.IMAGE"}}}, '
    '{"oclass": "CITY.IMAGE", "uid": "00000000-0000-0000-0000-000000000001", '
    '"attributes": {"path": "%s"}, '
    '"relationships": {"CITY.IS_PART_OF": {"00000000-0000-0000-0000-00000000002a": "CITY.CITY_WRAPPER"}}}], '
    '"deleted": [{"oclass": "CITY.IMAGE", "uid": "00000000-0000-0000-0000-000000000002", '
    '"attributes": {"path": "%s"}, "relationships": {}}], '
    '"expired": []}' % (FILE_PATHS[2], FILE_PATHS[0], FILE_PATHS[1])
)


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
        with open(FILE_PATHS[0], "wb") as f:
            f.write(("0" * 1024).encode("utf-8"))
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

    def setup_buffers1(self, session):
        wrapper = CITY.CITY_WRAPPER(session=session)
        images = wrapper.add(
            CITY.IMAGE(path=FILE_PATHS[0]),
            CITY.IMAGE(path=FILE_PATHS[1])
        )
        session._reset_buffers(BufferContext.USER)
        wrapper.remove(images[1].uid)
        images[0].path = FILE_PATHS[0]
        images = list(images) + \
            [wrapper.add(CITY.IMAGE(path=FILE_PATHS[2]))]
        session.prune()
        return images

    def test_serialize_buffers(self):
        # without providing target path
        with TransportSessionClient(SqliteSession, HOST, PORT) as session:
            self.setup_buffers1(session)
            _, result = serialize_buffers(
                session, buffer_context=BufferContext.USER,
                target_directory=None)
            self.assertEqual(
                sorted(map(os.path.abspath, [FILE_PATHS[0], FILE_PATHS[2]])),
                sorted(result)
            )

        # provide target path --> move files
        with TransportSessionClient(SqliteSession, HOST, PORT) as session:
            images = self.setup_buffers1(session)
            _, result = serialize_buffers(
                session, buffer_context=BufferContext.USER,
                target_directory=CLIENT_DIR)
            target = ["%s%s" % (image.uid, ending)
                      for image, ending in zip(images, ENDINGS)]
            target_full_path = [os.path.join(CLIENT_DIR, t) for t in target]
            self.assertEqual(
                sorted([target_full_path[0], target_full_path[2]]),
                sorted(result)
            )
            self.maxDiff = None

    def setup_buffers2(self, session):
        wrapper = CITY.CITY_WRAPPER(session=session, uid=42)
        images = wrapper.add(
            CITY.IMAGE(path=FILE_PATHS[0], uid=1),
            CITY.IMAGE(path=FILE_PATHS[1], uid=2)
        )
        session._reset_buffers(BufferContext.USER)
        return images

    def test_deserialize_buffers(self):
        with TransportSessionClient(SqliteSession, HOST, PORT) as session:
            images = self.setup_buffers2(session)
            deserialize_buffers(session, buffer_context=BufferContext.USER,
                                data=SERIALIZED_BUFFERS, temp_directory=None,
                                target_directory=CLIENT_DIR)
            added, updated, deleted = session._buffers[BufferContext.USER]
            self.assertEqual(len(added), 1)
            self.assertEqual(len(updated), 2)
            self.assertEqual(len(deleted), 1)
            images = images + [added[uuid.UUID(int=3)]]
            target = ["%s%s" % (image.uid, ending)
                      for image, ending in zip(images, ENDINGS)]
            target_full_path = [os.path.join(CLIENT_DIR, t) for t in target]
            self.assertEqual(added[uuid.UUID(int=3)].path,
                             target_full_path[2])
            self.assertEqual(updated[uuid.UUID(int=1)].path,
                             target_full_path[0])
            self.assertEqual(deleted[uuid.UUID(int=2)].path,
                             target_full_path[1])

    def test_get_file_cuds(self):
        image1 = CITY.IMAGE(path="x")
        image2 = CITY.IMAGE(path="y")
        city = CITY.CITY(name="Freiburg")
        x = {
            "a": image1,
            "b": 1,
            "c": None,
            "d": [city, image2]
        }
        r = get_file_cuds(x)
        self.assertEqual(r, [image1, image2])

    def test_encode_files(self):
        r = list(_encode_files(FILE_PATHS))
        self.maxDiff = None
        self.assertEqual(r, [])



if __name__ == "__main__":
    if sys.argv[-1] == "server":
        server = TransportSessionServer(SqliteSession, HOST, PORT,
                                        session_kwargs={"path": DB})
        server.startListening()
