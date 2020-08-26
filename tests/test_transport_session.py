import unittest2 as unittest
import uuid
import json
from copy import deepcopy
from osp.core.session.buffers import BufferContext, EngineContext, \
    BufferType
from osp.core.utils import create_recycle
from osp.core.session.wrapper_session import consumes_buffers
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer
from osp.core.session.transport.transport_utils import (
    deserialize, serializable, deserialize_buffers,
    serialize_buffers, LOAD_COMMAND, INITIALIZE_COMMAND
)
from osp.core.utils import create_from_cuds_object

try:
    from .test_session_city import TestWrapperSession
except ImportError:
    from test_session_city import TestWrapperSession

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

CUDS_DICT = {
    "oclass": "city.Citizen",
    "uid": str(uuid.UUID(int=123)),
    "attributes": {
        "name": "Peter",
        "age": 23
    },
    "relationships": {
        "city.INVERSE_OF_hasInhabitant": {str(uuid.UUID(int=1)): "city.City"},
        "city.hasChild": {str(uuid.UUID(int=2)): "city.Person",
                          str(uuid.UUID(int=3)): "city.Person"}
    }
}

ROOT_DICT = {
    "oclass": "city.CityWrapper",
    "uid": str(uuid.UUID(int=43)),
    "attributes": {},
    "relationships": {
        "city.hasPart": {str(uuid.UUID(int=1)): "city.City"}
    }
}

SERIALIZED_BUFFERS = {
    "added": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-000000000002",
        "attributes": {"name": "Paris",
                       "coordinates": [0, 0]},
        "relationships": {
            "city.isPartOf": {
                "00000000-0000-0000-0000-00000000007b": "city.CityWrapper"}}}],
    "updated": [{
        "oclass": "city.CityWrapper",
        "uid": "00000000-0000-0000-0000-00000000007b",
        "attributes": {},
        "relationships": {
            "city.hasPart":
                {"00000000-0000-0000-0000-000000000002":
                 "city.City"}}}],
    "deleted": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-000000000001",
        "attributes": {},
        "relationships": {}}],
    "expired": [],
    "args": [42],
    "kwargs": {"name": "London"}
}

SERIALIZED_BUFFERS_EXPIRED = {
    "added": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-000000000002",
        "attributes": {"name": "Paris",
                       "coordinates": [0, 0]},
        "relationships": {
            "city.isPartOf": {
                "00000000-0000-0000-0000-00000000007b": "city.CityWrapper"}}}],
    "updated": [{
        "oclass": "city.CityWrapper",
        "uid": "00000000-0000-0000-0000-00000000007b",
        "attributes": {},
        "relationships": {
            "city.hasPart": {
                "00000000-0000-0000-0000-000000000002": "city.City"}}}],
    "deleted": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-000000000001",
        "attributes": {},
        "relationships": {}}],
    "expired": [{"UUID": "00000000-0000-0000-0000-000000000003"}],
    "args": [42],
    "kwargs": {"name": "London"}
}

SERIALIZED_BUFFERS2 = {
    "added": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-00000000002a",
        "attributes": {"name": "London",
                       "coordinates": [0, 0]},
        "relationships": {}}],
    "updated": [], "deleted": [], "expired": []
}

SERIALIZED_BUFFERS3 = {
    "added": [{
        "oclass": "city.Citizen",
        "uid": "00000000-0000-0000-0000-000000000002",
        "attributes": {"name": "Peter", "age": 12},
        "relationships": {
            "city.INVERSE_OF_hasInhabitant": {
                "00000000-0000-0000-0000-000000000001": "city.City"}}}],
    "updated": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-000000000001",
        "attributes": {"name": "Freiburg",
                       "coordinates": [0, 0]},
        "relationships": {
            "city.isPartOf": {
                "00000000-0000-0000-0000-000000000003": "city.CityWrapper"},
            "city.hasInhabitant": {
                "00000000-0000-0000-0000-000000000002": "city.Citizen"}}}],
    "deleted": [], "expired": [],
    "result": [{
        "oclass": "city.City",
        "uid": "00000000-0000-0000-0000-000000000001",
        "attributes": {"name": "Freiburg",
                       "coordinates": [0, 0]},
        "relationships": {
            "city.isPartOf": {
                "00000000-0000-0000-0000-000000000003": "city.CityWrapper"},
            "city.hasInhabitant": {
                "00000000-0000-0000-0000-000000000002": "city.Citizen"}}}, {
        "oclass": "city.CityWrapper",
        "uid": "00000000-0000-0000-0000-000000000003",
        "attributes": {},
        "relationships": {
            "city.hasPart": {
                "00000000-0000-0000-0000-000000000001": "city.City"}}}]
}


class TestCommunicationEngineSharedFunctions(unittest.TestCase):

    def setUp(self):
        from osp.core.cuds import Cuds
        from osp.core.session import CoreSession
        Cuds._session = CoreSession()

    def testDeserialize(self):
        """Test transformation from normal dictionary to cuds"""
        with TestWrapperSession() as session:
            city.CityWrapper(session=session)
            cuds_object = deserialize(CUDS_DICT, session, True)
            self.assertEqual(cuds_object.uid.int, 123)
            self.assertEqual(cuds_object.name, "Peter")
            self.assertEqual(cuds_object.age, 23)
            self.assertEqual(cuds_object.oclass, city.Citizen)
            self.assertEqual(set(cuds_object._neighbors.keys()),
                             {city.INVERSE_OF_hasInhabitant,
                             city.hasChild})
            self.assertEqual(
                cuds_object._neighbors[city.INVERSE_OF_hasInhabitant],
                {uuid.UUID(int=1): city.City})
            self.assertEqual(cuds_object._neighbors[city.hasChild],
                             {uuid.UUID(int=2): city.Person,
                             uuid.UUID(int=3): city.Person})

            invalid_oclass = deepcopy(CUDS_DICT)
            invalid_oclass["oclass"] = "INVALID_OCLASS"
            self.assertRaises(ValueError, deserialize,
                              invalid_oclass, session, True)

            invalid_attribute = deepcopy(CUDS_DICT)
            invalid_attribute["attributes"]["invalid_attr"] = 0
            self.assertRaises(TypeError, deserialize,
                              invalid_attribute, session, True)

            invalid_rel = deepcopy(CUDS_DICT)
            invalid_rel["relationships"]["IS_INHABITANT_OF"] = {
                str(uuid.UUID(int=1)): "Person"}
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
                deserialize({"ENTITY": "city.Citizen"}, session, True),
                city.Citizen
            )
            self.assertEqual(
                deserialize([{"ENTITY": "city.Citizen"},
                             {"ENTITY": "city.City"}], session, True),
                [city.Citizen, city.City])
            self.assertEqual(deserialize([1, 1.2, "hallo"], session, True),
                             [1, 1.2, "hallo"])

    def test_serializable(self):
        """Test function to make Cuds objects json serializable"""
        p = city.Citizen(age=23,
                         name="Peter",
                         uid=uuid.UUID(int=123))
        c = city.City(name="Freiburg", uid=uuid.UUID(int=1))
        c1 = city.Person(uid=uuid.UUID(int=2))
        c2 = city.Person(uid=uuid.UUID(int=3))
        p.add(c, rel=city.INVERSE_OF_hasInhabitant)
        p.add(c1, c2, rel=city.hasChild)
        self.assertEqual(CUDS_DICT, serializable(p))
        self.assertEqual([CUDS_DICT], serializable([p]))
        self.assertEqual(None, serializable(None))
        self.assertEqual([None, None], serializable([None, None]))
        self.assertEqual({"UUID": "00000000-0000-0000-0000-000000000001"},
                         serializable(uuid.UUID(int=1)))
        self.assertEqual([{"UUID": "00000000-0000-0000-0000-000000000001"},
                          {"UUID": "00000000-0000-0000-0000-000000000002"}],
                         serializable([uuid.UUID(int=1), uuid.UUID(int=2)]))
        self.assertEqual({"ENTITY": "city.Citizen"},
                         serializable(city.Citizen))
        self.assertEqual([{"ENTITY": "city.Citizen"}, {"ENTITY": "city.City"}],
                         serializable([city.Citizen, city.City]))
        self.assertEqual([1, 1.2, "hallo"],
                         serializable([1, 1.2, "hallo"]))

    def test_deserialize_buffers(self):
        # buffer context user
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            p1 = city.Citizen(uid=uuid.UUID(int=3))
            p2 = city.Citizen(uid=uuid.UUID(int=4))
            c.add(p1, p2, rel=city.hasInhabitant)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)
            s1.expire(p2)

            additional = deserialize_buffers(
                s1,
                buffer_context=BufferContext.USER,
                data=json.dumps(SERIALIZED_BUFFERS_EXPIRED)
            )
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=123), uuid.UUID(int=2),
                              uuid.UUID(int=3), uuid.UUID(int=4)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1._neighbors[city.hasPart],
                             {cn.uid: city.City})
            self.assertEqual(set(ws1._neighbors.keys()), {city.hasPart})
            self.assertEqual(cn._neighbors[city.isPartOf],
                             {ws1.uid: city.CityWrapper})
            self.assertEqual(set(cn._neighbors.keys()), {city.isPartOf})
            self.assertEqual(s1._expired, {uuid.UUID(int=3), uuid.UUID(int=4)})
            self.assertEqual(s1._buffers, [
                [{cn.uid: cn}, {ws1.uid: ws1}, {c.uid: c}],
                [dict(), dict(), dict()]])

        # buffer context engine
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            p1 = city.Citizen(uid=uuid.UUID(int=3))
            p2 = city.Citizen(uid=uuid.UUID(int=4))
            c.add(p1, p2, rel=city.hasInhabitant)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)
            s1.expire(p2)

            additional = deserialize_buffers(
                s1, buffer_context=BufferContext.ENGINE,
                data=json.dumps(SERIALIZED_BUFFERS_EXPIRED)
            )
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [{cn.uid: cn}, {ws1.uid: ws1}, {c.uid: c}]])
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=123), uuid.UUID(int=2),
                              uuid.UUID(int=3), uuid.UUID(int=4)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1._neighbors[city.hasPart],
                             {cn.uid: city.City})
            self.assertEqual(set(ws1._neighbors.keys()), {city.hasPart})
            self.assertEqual(cn._neighbors[city.isPartOf],
                             {ws1.uid: city.CityWrapper})
            self.assertEqual(set(cn._neighbors.keys()), {city.isPartOf})
            self.assertEqual(s1._expired, {uuid.UUID(int=3), uuid.UUID(int=4)})
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [dict(), dict(), dict()]])

    def test_serialize_buffers(self):
        """ Test if serialization of buffers work """
        # no expiration
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            cn = city.City(name="Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            self.assertEqual(
                ('{"expired": [], "args": [42], "kwargs": {"name": "London"}}',
                 []),
                serialize_buffers(s1, buffer_context=None, additional_items={
                    "args": [42], "kwargs": {"name": "London"}})
            )
            added, updated, deleted = s1._buffers[BufferContext.USER]
            self.assertEqual(added.keys(), {uuid.UUID(int=2)})
            self.assertEqual(updated.keys(), {uuid.UUID(int=123)})
            self.assertEqual(deleted.keys(), {uuid.UUID(int=1)})
            self.assertEqual(s1._buffers[BufferContext.ENGINE],
                             [dict(), dict(), dict()])
            self.maxDiff = None
            result = serialize_buffers(
                s1, buffer_context=BufferContext.USER,
                additional_items={
                    "args": [42], "kwargs": {"name": "London"}
                }
            )
            self.assertEqual(json.loads(result[0]), SERIALIZED_BUFFERS)
            self.assertEqual(result[1], [])
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [dict(), dict(), dict()]
            ])
            s1._expired = {uuid.UUID(int=123), uuid.UUID(int=2)}

        # with expiration
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            cn = city.City(name="Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            s1._expired = {uuid.UUID(int=3)}
            self.assertEqual(
                ('{"expired": [{"UUID": '
                 '"00000000-0000-0000-0000-000000000003"}], '
                 '"args": [42], "kwargs": {"name": "London"}}', []),
                serialize_buffers(
                    s1,
                    buffer_context=None,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )
            added, updated, deleted = s1._buffers[BufferContext.USER]
            self.assertEqual(added.keys(), {uuid.UUID(int=2)})
            self.assertEqual(updated.keys(), {uuid.UUID(int=123)})
            self.assertEqual(deleted.keys(), {uuid.UUID(int=1)})
            self.assertEqual(s1._buffers[BufferContext.ENGINE],
                             [dict(), dict(), dict()])

            self.maxDiff = 3000
            result = serialize_buffers(
                s1,
                buffer_context=BufferContext.USER,
                additional_items={"args": [42],
                                  "kwargs": {"name": "London"}})
            self.assertEqual(
                SERIALIZED_BUFFERS_EXPIRED,
                json.loads(result[0])
            )
            self.assertEqual(
                [],
                result[1]
            )
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [dict(), dict(), dict()]
            ])
            s1._expired = {uuid.UUID(int=123), uuid.UUID(int=2)}


class MockEngine():
    def __init__(self, on_send=None):
        self.on_send = on_send
        self.uri = None

    def send(self, command, data, files=None):
        self._sent_command = command
        self._sent_data = data
        if self.on_send:
            return self.on_send(command, data)

    def close(self):
        pass


class TestCommunicationEngineClient(unittest.TestCase):
    def test_load(self):
        """ Test loading from server"""
        client = TransportSessionClient(TestWrapperSession, None)
        client.root = 1
        c1 = create_recycle(
            oclass=city.City,
            kwargs={"name": "Freiburg"},
            uid=1,
            session=client,
            fix_neighbors=False
        )
        c2 = city.City(name="London", uid=2)
        c3 = create_recycle(
            oclass=city.City,
            kwargs={"name": "Paris"},
            uid=3,
            session=client,
            fix_neighbors=False
        )
        client._reset_buffers(BufferContext.USER)
        client.expire(c3.uid)

        def on_send(command, data):
            with EngineContext(client):
                create_from_cuds_object(c2, client)
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
        self.assertEqual(client._buffers, [
            [dict(), dict(), dict()],
            [dict(), dict(), dict()]
        ])
        client.close()

    def test_store(self):
        """ Test storing of cuds_object. """
        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()

        # first item
        c1 = create_recycle(oclass=city.CityWrapper,
                            kwargs={},
                            uid=1,
                            session=client,
                            fix_neighbors=False)  # store will be called here
        self.assertEqual(client._engine._sent_command, INITIALIZE_COMMAND)
        self.assertEqual(client._engine._sent_data, (
            '{"args": [], "kwargs": {}, '
            '"root": {"oclass": "city.CityWrapper", '
            '"uid": "00000000-0000-0000-0000-000000000001", '
            '"attributes": {}, '
            '"relationships": {}}, "hashes": {}, "auth": null}'))
        self.assertEqual(set(client._registry.keys()), {c1.uid})

        # second item
        client._engine._sent_data = None
        client._engine._sent_command = None
        c2 = create_recycle(
            oclass=city.City,
            kwargs={"name": "Freiburg"},
            uid=2,
            session=client,
            fix_neighbors=False
        )
        self.assertEqual(client._engine._sent_command, None)
        self.assertEqual(client._engine._sent_data, None)
        self.assertEqual(set(client._registry.keys()), {c1.uid, c2.uid})
        client.close()

    def test_send(self):
        """ Test sending data to the server """
        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()
        client._send("command", True, "hello", bye="bye")
        self.assertEqual(client._engine._sent_command, "command")
        self.assertEqual(client._engine._sent_data, (
            '{"added": [], "updated": [], "deleted": [], "expired": [], '
            '"args": ["hello"], "kwargs": {"bye": "bye"}}'))
        client.close()

    def test_receive(self):
        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()
        w = city.CityWrapper(session=client)
        self.assertRaises(RuntimeError, client._receive, "ERROR: Error!", None)
        client._receive(json.dumps(SERIALIZED_BUFFERS2), None)
        self.assertEqual(set(client._registry.keys()), {uuid.UUID(int=42),
                                                        w.uid})
        self.assertEqual(client._buffers[BufferContext.USER],
                         [dict(), dict(), dict()])
        self.assertEqual(
            list(map(dict.keys, client._buffers[BufferContext.ENGINE])),
            [set([uuid.UUID(int=42)]), set(), set()]
        )
        client.close()

    def test_getattr(self):
        def command(*args, **kwargs):
            pass
        TestWrapperSession.command = consumes_buffers(command)

        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()
        client.command("arg1", "arg2", kwarg="kwarg")
        self.assertEqual(client._engine._sent_command, "command")
        self.assertEqual(client._engine._sent_data, (
            '{"added": [], "updated": [], "deleted": [], "expired": [], '
            '"args": ["arg1", "arg2"], "kwargs": {"kwarg": "kwarg"}}'))
        self.assertRaises(AttributeError, getattr, client, "run")
        client.close()


class TestCommunicationEngineServer(unittest.TestCase):

    def setUp(self):
        from osp.core.cuds import Cuds
        from osp.core.session import CoreSession
        Cuds._session = CoreSession()

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
            added = s._buffers[BufferContext.USER][BufferType.ADDED]
            correct = set(added.keys()) == {uuid.UUID(int=2)} and \
                added[uuid.UUID(int=2)].name == "Paris"
            s._reset_buffers(BufferContext.USER)

            added = s._buffers[BufferContext.ENGINE][BufferType.ADDED]
            added[uuid.UUID(int=uid)] = city.City(name=name,
                                                  uid=uid)

        TestWrapperSession.command = consumes_buffers(command)
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession() as s1:

            # initialize buffers
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            # test the method
            server.session_objs = {"1": s1, "2": 123}
            result = server._run_command(json.dumps(SERIALIZED_BUFFERS),
                                         "command", "1")
            self.assertTrue(correct)
            self.assertEqual(json.loads(result[0]), SERIALIZED_BUFFERS2)
            self.assertEqual(result[1], [])

    def test_load_from_session(self):
        """Test loading from the remote side"""
        with TestWrapperSession() as s1:
            c = city.City(name="Freiburg", uid=1)
            w = city.CityWrapper(session=s1, uid=3)
            cw = w.add(c)

            with EngineContext(s1):
                p = city.Citizen(name="Peter", age=12, uid=2)
                cw.add(p, rel=city.hasInhabitant)
                server = TransportSessionServer(TestWrapperSession, None, None)
                server.session_objs["user"] = s1
                s1._expired |= {c.uid, w.uid}
                result = server._load_from_session(
                    '{"uids": [{"UUID": 1}, {"UUID": 3}]}', "user")
            self.maxDiff = None
            self.assertEqual(json.loads(result[0]), SERIALIZED_BUFFERS3)
            self.assertEqual(result[1], [])

    def test_init_session(self):
        """Test the initialization of the session on the remote side"""
        server = TransportSessionServer(TestWrapperSession, None, None)
        data = json.dumps({
            "args": [],
            "kwargs": {},
            "root": ROOT_DICT,
            "hashes": {"test.py": "123"}
        })
        server.com_facility._file_hashes = {"user1": {}}
        server._init_session(data, connection_id="user1")
        self.assertEqual(server.session_objs["user1"].root, uuid.UUID(int=43))
        self.assertEqual(len(server.session_objs.keys()), 1)

        data = json.dumps({
            "args": ["invalid"],
            "kwargs": {},
            "root": CUDS_DICT
        })
        self.assertRaises(TypeError, server._init_session, data,
                          connection_id="user1")

    def test_handle_request(self):
        """Test if error message is returned when invalid command is given"""
        def command(s, age, name):
            raise RuntimeError("Something went wrong: %s, %s" % (age, name))
        TestWrapperSession.command = command
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession() as s1:
            # initialize buffers
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            # test
            server.session_objs["user1"] = s1
            self.assertEqual(server.handle_request(
                command="run", data=SERIALIZED_BUFFERS, connection_id="user1",
                temp_directory=None), ("ERROR: Invalid command", []))
            self.assertEqual(server.handle_request(
                command="command", data=json.dumps(SERIALIZED_BUFFERS),
                connection_id="user1",
                temp_directory=None),
                ("ERROR: RuntimeError: Something went wrong: 42, London", []))


if __name__ == '__main__':
    unittest.main()
