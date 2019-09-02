# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import asyncio
import uuid
import cuds.classes
from copy import deepcopy
from cuds.testing.test_session_city import TestWrapperSession
from cuds.classes.generated.cuba import CUBA
from cuds.classes.core.session.transport.transport_session import (
    to_cuds, serializable, buffers_to_registry, deserialize_buffers,
    serialize_buffers, TransportSessionServer, TransportSessionClient
)

CUDS_DICT = {
    "cuba_key": "CITIZEN",
    "attributes": {
                "uid": str(uuid.UUID(int=0)),
                "name": "Peter",
                "age": 23},
    "relationships": {
        "IS_INHABITANT_OF": {str(uuid.UUID(int=1)): "CITY"},
        "IS_PARENT_OF": {str(uuid.UUID(int=2)): "PERSON",
                         str(uuid.UUID(int=3)): "PERSON"}
    }
}

SERIALIZED_BUFFERS = (
    '{"added": [{'
    '"cuba_key": "CITY", '
    '"attributes": {"name": "Paris", '
    '"uid": "00000000-0000-0000-0000-000000000002"}, '
    '"relationships": {"IS_PART_OF": {"00000000-0000-0000-0000-000000000000": '
    '"CITY_WRAPPER"}}}], '
    '"updated": [{'
    '"cuba_key": "CITY_WRAPPER", '
    '"attributes": {"uid": "00000000-0000-0000-0000-000000000000"}, '
    '"relationships": {"HAS_PART": {"00000000-0000-0000-0000-000000000002": '
    '"CITY"}}}], '
    '"deleted": [{'
    '"cuba_key": "CITY", '
    '"attributes": {"name": "Freiburg", '
    '"uid": "00000000-0000-0000-0000-000000000001"}, '
    '"relationships": {}}], '
    '"args": [42], '
    '"kwargs": {"name": "London"}}')

SERIALIZED_BUFFERS2 = (
    '{"added": [{'
    '"cuba_key": "CITY", '
    '"attributes": {"name": "London", '
    '"uid": "00000000-0000-0000-0000-00000000002a"}, '
    '"relationships": {}}], "updated": [], "deleted": []}'
)

SERIALIZED_BUFFERS3 = (
    '{"added": [{"cuba_key": "CITY", '
    '"attributes": {"name": "Freiburg", '
    '"uid": "00000000-0000-0000-0000-000000000001"}, '
    '"relationships": {'
    '"HAS_INHABITANT": {"00000000-0000-0000-0000-000000000002": "CITIZEN"}, '
    '"IS_PART_OF": {"00000000-0000-0000-0000-000000000003": "CITY_WRAPPER"}}'
    '}, {"cuba_key": "CITY_WRAPPER", '
    '"attributes": {"uid": "00000000-0000-0000-0000-000000000003"}, '
    '"relationships": {'
    '"HAS_PART": {"00000000-0000-0000-0000-000000000001": "CITY"}}}], '
    '"deleted": [], "updated": []}'
)


class TestCommunicationEngineSharedFunctions(unittest.TestCase):

    def testToCuds(self):
        """Test transformation from normal dictionary to cuds object"""
        entity = to_cuds(CUDS_DICT)
        self.assertEqual(entity.uid.int, 0)
        self.assertEqual(entity.name, "Peter")
        self.assertEqual(entity.age, 23)
        self.assertEqual(entity.cuba_key, CUBA.CITIZEN)
        self.assertEqual(set(entity.keys()),
                         {cuds.classes.IsInhabitantOf,
                          cuds.classes.IsParentOf})
        self.assertEqual(entity[cuds.classes.IsInhabitantOf],
                         {uuid.UUID(int=1): CUBA.CITY})
        self.assertEqual(entity[cuds.classes.IsParentOf],
                         {uuid.UUID(int=2): CUBA.PERSON,
                          uuid.UUID(int=3): CUBA.PERSON})

        invalid_cuba = deepcopy(CUDS_DICT)
        invalid_cuba["cuba_key"] = "INVALID_CUBA"
        self.assertRaises(ValueError, to_cuds, invalid_cuba)

        invalid_attribute = deepcopy(CUDS_DICT)
        invalid_attribute["attributes"]["invalid_attr"] = 0
        self.assertRaises(TypeError, to_cuds, invalid_attribute)

        invalid_rel = deepcopy(CUDS_DICT)
        invalid_rel["relationships"]["IS_INHABITANT_OF"] = {
            str(uuid.UUID(int=1)): "PERSON"}
        self.assertRaises(ValueError, to_cuds, invalid_rel)

    def test_serializable(self):
        """Test function to make Cuds objects json serializable"""
        p = cuds.classes.Citizen(age=23,
                                 name="Peter",
                                 uid=uuid.UUID(int=0))
        c = cuds.classes.City(name="Freiburg", uid=uuid.UUID(int=1))
        c1 = cuds.classes.Person(uid=uuid.UUID(int=2))
        c2 = cuds.classes.Person(uid=uuid.UUID(int=3))
        p.add(c, rel=cuds.classes.IsInhabitantOf)
        p.add(c1, c2, rel=cuds.classes.IsParentOf)
        self.assertEqual(CUDS_DICT, serializable(p))

    def test_buffers_to_registry(self):
        """Test method that pushes buffer changes to the registry"""
        with TestWrapperSession() as s1:
            with TestWrapperSession() as s2:
                ws1 = cuds.classes.CityWrapper(session=s1)
                ws2 = cuds.classes.CityWrapper(session=s2, uid=ws1.uid)
                c = cuds.classes.City("Freiburg")
                ws1.add(c)
                ws2.add(c)
                s1._reset_buffers(changed_by="user")
                s2._reset_buffers(changed_by="user")

                cn = cuds.classes.City("Paris")
                ws1.add(cn)
                ws1.remove(c.uid)
                s1.prune()

                s2._added = s1._added
                s2._updated = s1._updated
                s2._deleted = s1._deleted
                buffers_to_registry(s2)

                self.assertEqual(s1._registry, s2._registry)
                self.assertEqual(set(s2._registry.keys()), {ws1.uid, cn.uid})
                self.assertEqual([x.uid for x in ws2.get()], [cn.uid])

    def test_deserialize_buffers(self):
        with TestWrapperSession() as s1:
            ws1 = cuds.classes.CityWrapper(session=s1, uid=0)
            c = cuds.classes.City("Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            additional = deserialize_buffers(s1, SERIALIZED_BUFFERS)
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=0), uuid.UUID(int=2)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1[cuds.classes.HasPart], {cn.uid: CUBA.CITY})
            self.assertEqual(set(ws1.keys()), {cuds.classes.HasPart})
            self.assertEqual(cn[cuds.classes.IsPartOf],
                             {ws1.uid: CUBA.CITY_WRAPPER})
            self.assertEqual(set(cn.keys()), {cuds.classes.IsPartOf})

    def test_serialize_buffers(self):
        """ Test if serialization of buffers work """
        with TestWrapperSession() as s1:
            ws1 = cuds.classes.CityWrapper(session=s1, uid=0)
            c = cuds.classes.City("Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            cn = cuds.classes.City("Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            self.maxDiff = 2000
            self.assertEqual(
                SERIALIZED_BUFFERS,
                serialize_buffers(
                    s1,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )


class TestCommunicationEngineClient(unittest.TestCase):
    def test_load(self):
        pass

    def test_store(self):
        pass

    def test_send(self):
        pass

    def test_receive(self):
        pass

    def test_getattr(self):
        pass


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
        correct = False

        # command to be executed
        def command(s, uid, name):
            nonlocal correct
            correct = set(s._added.keys()) == {uuid.UUID(int=2)} and \
                s._added[uuid.UUID(int=2)].name == "Paris"
            s._reset_buffers(changed_by="user")
            s._added[uuid.UUID(int=uid)] = cuds.classes.City(name=name,
                                                             uid=uid)
            s._reset_buffers(changed_by="engine")

        TestWrapperSession.command = command
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession(forbid_buffer_reset_by="engine") as s1:

            # initialize buffers
            ws1 = cuds.classes.CityWrapper(session=s1, uid=0)
            c = cuds.classes.City("Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(changed_by="user")

            # test the method
            server.session_objs = {"1": s1, "2": 123}
            result = server._run_command(SERIALIZED_BUFFERS, "command", "1")
            self.assertTrue(correct)
            self.assertEqual(result, SERIALIZED_BUFFERS2)

    def test_load_from_session(self):
        with TestWrapperSession(forbid_buffer_reset_by="engine") as s1:
            c = cuds.classes.City("Freiburg", uid=1)
            p = cuds.classes.Citizen(name="Peter", age=12, uid=2)
            w = cuds.classes.CityWrapper(session=s1, uid=3)
            c.add(p, rel=cuds.classes.HasInhabitant)
            w.add(c)
            server = TransportSessionServer(TestWrapperSession, None, None)
            server.session_objs["user"] = s1
            result = server._load_from_session("[1, 3]", "user")
            print(result)

    def test_init_session(self):
        pass

    def test_handle_request(self):
        pass


if __name__ == '__main__':
    unittest.main()
