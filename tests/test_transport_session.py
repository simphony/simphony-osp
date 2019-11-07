# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import uuid
import json
from copy import deepcopy
from osp.core import CITY
from osp.core.utils import create_recycle
from osp.core.session.wrapper_session import consumes_buffers
from .test_session_city import TestWrapperSession
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer
from osp.core.session.transport.transport_util import (
    deserialize, serializable, deserialize_buffers,
    serialize, LOAD_COMMAND, INITIALIZE_COMMAND
)
from osp.core.utils import create_from_cuds_object

CUDS_DICT = {
    "is_a": "CITY.CITIZEN",
    "uid": str(uuid.UUID(int=0)),
    "attributes": {
        "name": "Peter",
        "age": 23
    },
    "relationships": {
        "CITY.IS_INHABITANT_OF": {str(uuid.UUID(int=1)): "CITY.CITY"},
        "CITY.HAS_CHILD": {str(uuid.UUID(int=2)): "CITY.PERSON",
                           str(uuid.UUID(int=3)): "CITY.PERSON"}
    }
}

SERIALIZED_BUFFERS = (
    '{"added": [{'
    '"is_a": "CITY.CITY", '
    '"uid": "00000000-0000-0000-0000-000000000002", '
    '"attributes": {"name": "Paris", '
    '"coordinates": [0, 0]}, '
    '"relationships": {"CITY.IS_PART_OF": {"00000000-0000-0000-0000-000000000000": '
    '"CITY.CITY_WRAPPER"}}}], '
    '"updated": [{'
    '"is_a": "CITY.CITY_WRAPPER", "uid": "00000000-0000-0000-0000-000000000000", '
    '"attributes": {}, '
    '"relationships": {"CITY.HAS_PART": {"00000000-0000-0000-0000-000000000002": '
    '"CITY.CITY"}}}], '
    '"deleted": [{'
    '"is_a": "CITY.CITY", '
    '"uid": "00000000-0000-0000-0000-000000000001", '
    '"attributes": {"name": "Freiburg", '
    '"coordinates": [0, 0]}, '
    '"relationships": {}}], '
    '"args": [42], '
    '"kwargs": {"name": "London"}}'
)

SERIALIZED_BUFFERS_EXPIRED = (
    '{"added": [{'
    '"is_a": "CITY.CITY", '
    '"uid": "00000000-0000-0000-0000-000000000002", '
    '"attributes": {"name": "Paris", '
    '"coordinates": [0, 0]}, '
    '"relationships": {"CITY.IS_PART_OF": {"00000000-0000-0000-0000-000000000000": '
    '"CITY.CITY_WRAPPER"}}}], '
    '"updated": [{'
    '"is_a": "CITY.CITY_WRAPPER", "uid": "00000000-0000-0000-0000-000000000000", '
    '"attributes": {}, '
    '"relationships": {"CITY.HAS_PART": {"00000000-0000-0000-0000-000000000002": '
    '"CITY.CITY"}}}], '
    '"deleted": [{'
    '"is_a": "CITY.CITY", '
    '"uid": "00000000-0000-0000-0000-000000000001", '
    '"attributes": {"name": "Freiburg", '
    '"coordinates": [0, 0]}, '
    '"relationships": {}}], '
    '"expired": [{"UUID": "00000000-0000-0000-0000-000000000003"}], '
    '"args": [42], '
    '"kwargs": {"name": "London"}}'
)

SERIALIZED_BUFFERS2 = (
    '{"added": [{'
    '"is_a": "CITY.CITY", '
    '"uid": "00000000-0000-0000-0000-00000000002a", '
    '"attributes": {"name": "London", '
    '"coordinates": [0, 0]}, '
    '"relationships": {}}], "updated": [], "deleted": []}'
)

SERIALIZED_BUFFERS3 = (
    '{"result": [{"is_a": "CITY.CITY", '
    '"uid": "00000000-0000-0000-0000-000000000001", '
    '"attributes": {"name": "Freiburg", '
    '"coordinates": [0, 0]}, '
    '"relationships": {'
    '"CITY.HAS_INHABITANT": {"00000000-0000-0000-0000-000000000002": "CITY.CITIZEN"}, '
    '"CITY.IS_PART_OF": {"00000000-0000-0000-0000-000000000003": "CITY.CITY_WRAPPER"}}'
    '}, {"is_a": "CITY.CITY_WRAPPER", "uid": "00000000-0000-0000-0000-000000000003", '
    '"attributes": {}, '
    '"relationships": {'
    '"CITY.HAS_PART": {"00000000-0000-0000-0000-000000000001": "CITY.CITY"}}}], '
    '"added": [], "deleted": [], "updated": []}'
)


class TestCommunicationEngineSharedFunctions(unittest.TestCase):

    def testDeserialize(self):
        """Test transformation from normal dictionary to cuds"""
        with TestWrapperSession() as session:
            cuds_object = deserialize(CUDS_DICT, session, True)
            self.assertEqual(cuds_object.uid.int, 0)
            self.assertEqual(cuds_object.name, "Peter")
            self.assertEqual(cuds_object.age, 23)
            self.assertEqual(cuds_object.is_a, CITY.CITIZEN)
            self.assertEqual(set(cuds_object._neighbours.keys()),
                             {CITY.IS_INHABITANT_OF,
                             CITY.HAS_CHILD})
            self.assertEqual(cuds_object._neighbours[CITY.IS_INHABITANT_OF],
                             {uuid.UUID(int=1): CITY.CITY})
            self.assertEqual(cuds_object._neighbours[CITY.HAS_CHILD],
                             {uuid.UUID(int=2): CITY.PERSON,
                             uuid.UUID(int=3): CITY.PERSON})

            invalid_cuba = deepcopy(CUDS_DICT)
            invalid_cuba["is_a"] = "INVALID_CUBA"
            self.assertRaises(ValueError, deserialize,
                              invalid_cuba, session, True)

            invalid_attribute = deepcopy(CUDS_DICT)
            invalid_attribute["attributes"]["invalid_attr"] = 0
            self.assertRaises(TypeError, deserialize,
                              invalid_attribute, session, True)

            invalid_rel = deepcopy(CUDS_DICT)
            invalid_rel["relationships"]["IS_INHABITANT_OF"] = {
                str(uuid.UUID(int=1)): "PERSON"}
            self.assertRaises(ValueError, deserialize,
                              invalid_rel, session, True)

            self.assertEqual(deserialize(None, session, True), None)
            self.assertEqual(deserialize([None, None], session, True),
                             [None, None])
            self.assertEqual(
                deserialize({"UUID": "00000000-0000-0000-0000-000000000001"},
                            session, True), uuid.UUID(int=1))
            self.assertEqual(
                deserialize(
                    [{"UUID": "00000000-0000-0000-0000-000000000001"},
                     {"UUID": "00000000-0000-0000-0000-000000000002"}],
                    session, True),
                [uuid.UUID(int=1), uuid.UUID(int=2)])
            self.assertEqual(
                deserialize({"ENTITY": "CITY.CITIZEN"}, session, True),
                CITY.CITIZEN
            )
            self.assertEqual(
                deserialize([{"ENTITY": "CITY.CITIZEN"},
                             {"ENTITY": "CITY.CITY"}], session, True),
                [CITY.CITIZEN, CITY.CITY])
            self.assertEqual(deserialize([1, 1.2, "hallo"], session, True),
                             [1, 1.2, "hallo"])

    def test_serializable(self):
        """Test function to make Cuds objects json serializable"""
        p = CITY.CITIZEN(age=23,
                                 name="Peter",
                                 uid=uuid.UUID(int=0))
        c = CITY.CITY(name="Freiburg", uid=uuid.UUID(int=1))
        c1 = CITY.PERSON(uid=uuid.UUID(int=2))
        c2 = CITY.PERSON(uid=uuid.UUID(int=3))
        p.add(c, rel=CITY.IS_INHABITANT_OF)
        p.add(c1, c2, rel=CITY.HAS_CHILD)
        self.assertEqual(CUDS_DICT, serializable(p))
        self.assertEqual([CUDS_DICT], serializable([p]))
        self.assertEqual(None, serializable(None))
        self.assertEqual([None, None], serializable([None, None]))
        self.assertEqual({"UUID": "00000000-0000-0000-0000-000000000001"},
                         serializable(uuid.UUID(int=1)))
        self.assertEqual([{"UUID": "00000000-0000-0000-0000-000000000001"},
                          {"UUID": "00000000-0000-0000-0000-000000000002"}],
                         serializable([uuid.UUID(int=1), uuid.UUID(int=2)]))
        self.assertEqual({"ENTITY": "CITY.CITIZEN"},
                         serializable(CITY.CITIZEN))
        self.assertEqual([{"ENTITY": "CITY.CITIZEN"}, {"ENTITY": "CITY.CITY"}],
                         serializable([CITY.CITIZEN, CITY.CITY]))
        self.assertEqual([1, 1.2, "hallo"],
                         serializable([1, 1.2, "hallo"]))

    def test_deserialize_buffers(self):
        # no reset
        with TestWrapperSession() as s1:
            s1._expired = {uuid.UUID(int=4)}
            ws1 = CITY.CITY_WRAPPER(session=s1, uid=0)
            c = CITY.CITY(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            additional = deserialize_buffers(s1, SERIALIZED_BUFFERS_EXPIRED,
                                             add_to_buffers=True)
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=0), uuid.UUID(int=2)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1._neighbours[CITY.HAS_PART], {cn.uid: CITY.CITY})
            self.assertEqual(set(ws1._neighbours.keys()), {CITY.HAS_PART})
            self.assertEqual(cn._neighbours[CITY.IS_PART_OF],
                             {ws1.uid: CITY.CITY_WRAPPER})
            self.assertEqual(set(cn._neighbours.keys()), {CITY.IS_PART_OF})
            self.assertEqual(s1._expired, {uuid.UUID(int=3), uuid.UUID(int=4)})
            self.assertEqual(s1._added, {cn.uid: cn})
            self.assertEqual(s1._updated, {ws1.uid: ws1})
            self.assertEqual(s1._deleted, {c.uid: c})
            self.assertEqual(s1._uids_in_registry_after_last_buffer_reset,
                             {ws1.uid, c.uid})

        # with reset
        with TestWrapperSession() as s1:
            s1._expired = {uuid.UUID(int=4)}
            ws1 = CITY.CITY_WRAPPER(session=s1, uid=0)
            c = CITY.CITY(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            additional = deserialize_buffers(s1, SERIALIZED_BUFFERS_EXPIRED,
                                             add_to_buffers=False)
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=0), uuid.UUID(int=2)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1._neighbours[CITY.HAS_PART], {cn.uid: CITY.CITY})
            self.assertEqual(set(ws1._neighbours.keys()), {CITY.HAS_PART})
            self.assertEqual(cn._neighbours[CITY.IS_PART_OF],
                             {ws1.uid: CITY.CITY_WRAPPER})
            self.assertEqual(set(cn._neighbours.keys()), {CITY.IS_PART_OF})
            self.assertEqual(s1._expired, {uuid.UUID(int=3), uuid.UUID(int=4)})
            self.assertEqual(s1._added, dict())
            self.assertEqual(s1._updated, dict())
            self.assertEqual(s1._deleted, dict())
            self.assertEqual(s1._uids_in_registry_after_last_buffer_reset,
                             {cn.uid, c.uid, ws1.uid})

    def test_serialize(self):
        """ Test if serialization of buffers work """
        # no expiration
        with TestWrapperSession() as s1:
            ws1 = CITY.CITY_WRAPPER(session=s1, uid=0)
            c = CITY.CITY(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            cn = CITY.CITY(name="Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            self.assertEqual(
                '{"args": [42], "kwargs": {"name": "London"}}',
                serialize(
                    s1,
                    consume_buffers=False,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )
            self.assertEqual(s1._added.keys(), {uuid.UUID(int=2)})
            self.assertEqual(s1._updated.keys(), {uuid.UUID(int=0)})
            self.assertEqual(s1._deleted.keys(), {uuid.UUID(int=1)})
            self.maxDiff = None
            self.assertEqual(
                SERIALIZED_BUFFERS,
                serialize(
                    s1,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )
            self.assertEqual(s1._added.keys(), set())
            self.assertEqual(s1._updated.keys(), set())
            self.assertEqual(s1._deleted.keys(), set())
            s1._expired = {uuid.UUID(int=0), uuid.UUID(int=2)}

        # with expiration
        with TestWrapperSession() as s1:
            ws1 = CITY.CITY_WRAPPER(session=s1, uid=0)
            c = CITY.CITY(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            cn = CITY.CITY(name="Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            s1._expired = {uuid.UUID(int=3)}
            self.assertEqual(
                '{"expired": [{"UUID": '
                '"00000000-0000-0000-0000-000000000003"}], '
                '"args": [42], "kwargs": {"name": "London"}}',
                serialize(
                    s1,
                    consume_buffers=False,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )
            self.assertEqual(s1._added.keys(), {uuid.UUID(int=2)})
            self.assertEqual(s1._updated.keys(), {uuid.UUID(int=0)})
            self.assertEqual(s1._deleted.keys(), {uuid.UUID(int=1)})

            self.maxDiff = 3000
            self.assertEqual(
                SERIALIZED_BUFFERS_EXPIRED,
                serialize(
                    s1,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )
            self.assertEqual(s1._added.keys(), set())
            self.assertEqual(s1._updated.keys(), set())
            self.assertEqual(s1._deleted.keys(), set())
            s1._expired = {uuid.UUID(int=0), uuid.UUID(int=2)}


class MockEngine():
    def __init__(self, on_send=None):
        self.on_send = on_send

    def send(self, command, data):
        self._sent_command = command
        self._sent_data = data
        if self.on_send:
            return self.on_send(command, data)


class TestCommunicationEngineClient(unittest.TestCase):
    def test_load(self):
        """ Test loading from server"""
        client = TransportSessionClient(TestWrapperSession, None, None)
        client.root = 1
        c1 = create_recycle(
            entity_cls=CITY.CITY,
            kwargs={"name": "Freiburg"},
            uid=1,
            session=client,
            add_to_buffers=True
        )
        c2 = CITY.CITY(name="London", uid=2)
        c3 = create_recycle(
            entity_cls=CITY.CITY,
            kwargs={"name": "Paris"},
            uid=3,
            session=client,
            add_to_buffers=True
        )
        client.expire(c3.uid)
        client._reset_buffers(changed_by="user")

        def on_send(command, data):
            create_from_cuds_object(c2, client, False)
            return [c2, None]

        client._engine = MockEngine(on_send)
        result = list(client.load(uuid.UUID(int=1),
                                  uuid.UUID(int=2),
                                  uuid.UUID(int=3)))
        self.assertEqual(client._engine._sent_command, LOAD_COMMAND)
        self.assertEqual(
            client._engine._sent_data,
            '{"expired": [{"UUID": "00000000-0000-0000-0000-000000000003"}], '
            '"uids": [{"UUID": "00000000-0000-0000-0000-000000000002"}, '
            '{"UUID": "00000000-0000-0000-0000-000000000003"}]}')
        self.assertEqual(result, [c1, c2, None])
        self.assertEqual(set(client._registry.keys()), {c1.uid, c2.uid})
        self.assertEqual(client._uids_in_registry_after_last_buffer_reset,
                         {c1.uid, c2.uid, c3.uid})
        self.assertEqual(client._added, dict())
        self.assertEqual(client._updated, dict())
        self.assertEqual(client._deleted, dict())

    def test_store(self):
        """ Test storing of cuds_object. """
        client = TransportSessionClient(TestWrapperSession, None, None)
        client._engine = MockEngine()

        # first item
        c1 = create_recycle(entity_cls=CITY.CITY,
                            kwargs={"name": "Freiburg"},
                            uid=1,
                            session=client,
                            add_to_buffers=True)  # store will be called here
        self.assertEqual(client._engine._sent_command, INITIALIZE_COMMAND)
        self.assertEqual(client._engine._sent_data, (
            '{"args": [], "kwargs": {}, '
            '"root": {"is_a": "CITY.CITY", '
            '"uid": "00000000-0000-0000-0000-000000000001", "attributes": {"name": "Freiburg", '
            '"coordinates": [0, 0]}, '
            '"relationships": {}}}'))
        self.assertEqual(set(client._registry.keys()), {c1.uid})

        # second item
        client._engine._sent_data = None
        client._engine._sent_command = None
        c2 = create_recycle(
            entity_cls=CITY.CITY,
            kwargs={"name": "Freiburg"},
            uid=1,
            session=client,
            add_to_buffers=True)

        self.assertEqual(client._engine._sent_command, None)
        self.assertEqual(client._engine._sent_data, None)
        self.assertEqual(set(client._registry.keys()), {c1.uid, c2.uid})

    def test_send(self):
        """ Test sending data to the server """
        client = TransportSessionClient(TestWrapperSession, None, None)
        client._engine = MockEngine()
        client._send("command", True, "hello", bye="bye")
        self.assertEqual(client._engine._sent_command, "command")
        self.assertEqual(client._engine._sent_data, (
            '{"added": [], "updated": [], "deleted": [], "expired": [], '
            '"args": ["hello"], "kwargs": {"bye": "bye"}}'))

    def test_receive(self):
        client = TransportSessionClient(TestWrapperSession, None, None)
        client._engine = MockEngine()
        self.assertRaises(RuntimeError, client._receive, "ERROR: Error!")
        client._receive(SERIALIZED_BUFFERS2)
        self.assertEqual(set(client._registry.keys()), {uuid.UUID(int=42)})
        self.assertEqual(client._added, dict())
        self.assertEqual(client._updated, dict())
        self.assertEqual(client._deleted, dict())

    def test_getattr(self):
        def command(*args, **kwargs):
            pass
        TestWrapperSession.command = consumes_buffers(command)

        client = TransportSessionClient(TestWrapperSession, None, None)
        client._engine = MockEngine()
        client.command("arg1", "arg2", kwarg="kwarg")
        self.assertEqual(client._engine._sent_command, "command")
        self.assertEqual(client._engine._sent_data, (
            '{"added": [], "updated": [], "deleted": [], "expired": [], '
            '"args": ["arg1", "arg2"], "kwargs": {"kwarg": "kwarg"}}'))
        self.assertRaises(AttributeError, getattr, client, "run")


class TestCommunicationEngineServer(unittest.TestCase):
    def test_handle_disconnect(self):
        """Test the behavior when a user disconnects. """
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession() as s1:
            closed = False

            def close():
                nonlocal closed
                closed = True
            s1.close = close
            server.session_objs = {"1": s1, "2": 123}
            server.handle_disconnect("1")
            self.assertTrue(closed)
            self.assertEqual(server.session_objs, {"2": 123})

    def test_run_command(self):
        """Test to run a command"""
        correct = False

        # command to be executed
        def command(s, uid, name):
            nonlocal correct
            correct = set(s._added.keys()) == {uuid.UUID(int=2)} and \
                s._added[uuid.UUID(int=2)].name == "Paris"
            s._reset_buffers(changed_by="user")
            s._added[uuid.UUID(int=uid)] = CITY.CITY(name=name,
                                                             uid=uid)
            s._reset_buffers(changed_by="engine")

        TestWrapperSession.command = command
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession(forbid_buffer_reset_by="engine") as s1:

            # initialize buffers
            ws1 = CITY.CITY_WRAPPER(session=s1, uid=0)
            c = CITY.CITY(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            # test the method
            server.session_objs = {"1": s1, "2": 123}
            result = server._run_command(SERIALIZED_BUFFERS, "command", "1")
            self.assertTrue(correct)
            self.assertEqual(result, SERIALIZED_BUFFERS2)

    def test_load_from_session(self):
        """Test loading from the remote side"""
        with TestWrapperSession(forbid_buffer_reset_by="engine") as s1:
            c = CITY.CITY(name="Freiburg", uid=1)
            p = CITY.CITIZEN(name="Peter", age=12, uid=2)
            w = CITY.CITY_WRAPPER(session=s1, uid=3)
            c.add(p, rel=CITY.HAS_INHABITANT)
            w.add(c)
            server = TransportSessionServer(TestWrapperSession, None, None)
            server.session_objs["user"] = s1
            result = server._load_from_session(
                '{"uids": [{"UUID": 1}, {"UUID": 3}]}', "user")
            self.assertEqual(result, SERIALIZED_BUFFERS3)

    def test_init_session(self):
        """Test the initialization of the session on the remote side"""
        server = TransportSessionServer(TestWrapperSession, None, None)
        data = json.dumps({
            "args": [],
            "kwargs": {},
            "root": CUDS_DICT
        })
        server._init_session(data, user="user1")
        self.assertEqual(server.session_objs["user1"].root, uuid.UUID(int=0))
        self.assertEqual(len(server.session_objs.keys()), 1)

        data = json.dumps({
            "args": ["invalid"],
            "kwargs": {},
            "root": CUDS_DICT
        })
        self.assertRaises(TypeError, server._init_session, data, user="user1")

    def test_handle_request(self):
        """Test if error message is returned when invalid command is given"""
        def command(s, age, name):
            raise RuntimeError("Something went wrong: %s, %s" % (age, name))
        TestWrapperSession.command = command
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession(forbid_buffer_reset_by="engine") as s1:
            # initialize buffers
            ws1 = CITY.CITY_WRAPPER(session=s1, uid=0)
            c = CITY.CITY(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            # test
            server.session_objs["user1"] = s1
            self.assertEqual(server.handle_request(
                "run", SERIALIZED_BUFFERS, "user1"), "ERROR: Invalid command")
            self.assertEqual(server.handle_request(
                "command", SERIALIZED_BUFFERS, "user1"),
                "ERROR: RuntimeError: Something went wrong: 42, London")


if __name__ == '__main__':
    unittest.main()
