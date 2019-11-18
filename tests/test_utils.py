# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import io
import unittest
import responses
import osp.core
from osp.core import CITY, CUBA
from osp.core.session.transport.transport_util import serializable
from osp.core.session.core_session import CoreSession
from .dummy_simulation_wrapper import DummySimWrapperSession
from osp.core.utils import (
    destroy_cuds_object, clone_cuds_object,
    create_recycle, create_from_cuds_object,
    check_arguments, format_class_name, find_cuds_object,
    find_cuds_object_by_uid, remove_cuds_object,
    pretty_print,
    find_cuds_objects_by_oclass, find_relationships,
    find_cuds_objects_by_attribute, post,
    get_relationships_between,
    get_neighbour_diff
)
from osp.core.cuds import Cuds


def get_test_city():
    """helper function"""
    c = CITY.CITY(name="Freiburg", coordinates=[1, 2])
    p1 = CITY.CITIZEN(name="Rainer")
    p2 = CITY.CITIZEN(name="Carlos")
    p3 = CITY.CITIZEN(name="Maria")
    n1 = CITY.NEIGHBOURHOOD(name="Zähringen", coordinates=[2, 3])
    n2 = CITY.NEIGHBOURHOOD(name="St. Georgen", coordinates=[3, 4])
    s1 = CITY.STREET(name="Lange Straße", coordinates=[4, 5])

    c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
    p1.add(p3, rel=CITY.HAS_CHILD)
    p2.add(p3, rel=CITY.HAS_CHILD)
    c.add(n1, n2)
    n1.add(s1)
    n2.add(s1)
    s1.add(p2, p3, rel=CITY.HAS_INHABITANT)
    return [c, p1, p2, p3, n1, n2, s1]


class TestUtils(unittest.TestCase):

    @responses.activate
    def test_post(self):
        """Test sending a cuds object to the server"""
        def request_callback(request):
            headers = {'request-id': '728d329e-0e86-11e4-a748-0c84dc037c13'}
            return (200, headers, request.body)

        responses.add_callback(
            responses.POST, 'http://dsms.com',
            callback=request_callback,
            content_type='application/json',
        )

        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        response = post('http://dsms.com', c)

        serialized = serializable([c, p1, p2, p3, n1, n2, s1])
        for x in response.json():
            i = serialized.index(x)
            del serialized[i]
        self.assertEqual(serialized, list())

        response = post('http://dsms.com', c, max_depth=1)
        serialized = serializable([c, p1, p2, p3, n1, n2])
        for x in response.json():
            i = serialized.index(x)
            del serialized[i]
        self.assertEqual(serialized, list())

    def test_destroy_cuds_object(self):
        """Test destroying of cuds"""
        a = CITY.CITY(name="Freiburg")
        b = CITY.CITIZEN(age=12, name="Horst")
        with CoreSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            aw = w.add(a)
            bw = aw.add(b, rel=CITY.HAS_INHABITANT)
            session._expired = {bw.uid}
            destroy_cuds_object(aw)

            self.assertEqual(a.name, "Freiburg")
            self.assertEqual(bw.name, "Horst")
            self.assertFalse(hasattr(aw, "name"))
            self.assertEqual(aw.get(), [])

            destroy_cuds_object(bw)
            self.assertFalse(hasattr(bw, "name"))
            self.assertEqual(session._expired, set())

    def test_clone_cuds_object(self):
        """Test cloning of cuds"""
        a = CITY.CITY(name="Freiburg")
        with CoreSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            aw = w.add(a)
            clone = clone_cuds_object(aw)
            self.assertIsNot(aw, None)
            self.assertIs(clone.session, aw.session)
            self.assertEqual(clone.uid, aw.uid)
            self.assertIs(aw, session._registry.get(aw.uid))
            self.assertEqual(clone.name, "Freiburg")

    def test_create_recycle(self):
        """Test creation of cuds_objects for different session"""
        default_session = CoreSession()
        osp.core.cuds.Cuds._session = default_session
        a = CITY.CITY(name="Freiburg")
        self.assertIs(a.session, default_session)
        with DummySimWrapperSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            b = create_recycle(
                oclass=CITY.CITY,
                kwargs={"name": "Offenburg"},
                uid=a.uid,
                session=session,
                add_to_buffers=False)
            self.assertEqual(b.name, "Offenburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid, w.uid})
            self.assertIs(session._registry.get(b.uid), b)
            self.assertEqual(session._added, {w.uid: w})
            self.assertEqual(
                session._uids_in_registry_after_last_buffer_reset, {b.uid}
            )

            x = CITY.CITIZEN()
            b.add(x, rel=CITY.HAS_INHABITANT)

            c = create_recycle(oclass=CITY.CITY,
                               kwargs={"name": "Emmendingen"},
                               session=session, uid=a.uid,
                               add_to_buffers=True)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Emmendingen")
            self.assertEqual(c.get(rel=CUBA.RELATIONSHIP), [])
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(session._updated, {c.uid: c})

    def test_create_from_cuds_object(self):
        """Test copying cuds_objects to different session"""
        default_session = CoreSession()
        Cuds._session = default_session
        a = CITY.CITY(name="Freiburg")
        self.assertIs(a.session, default_session)
        with DummySimWrapperSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            b = create_from_cuds_object(a, session, False)
            self.assertEqual(b.name, "Freiburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid, w.uid})
            self.assertIs(session._registry.get(b.uid), b)
            self.assertEqual(session._added, {w.uid: w})

            b.name = "Emmendingen"
            x = CITY.CITIZEN(age=54, name="Franz")
            b.add(x, rel=CITY.HAS_INHABITANT)
            y = CITY.CITIZEN(age=21, name="Rolf")
            a.add(y, rel=CITY.HAS_INHABITANT)

            c = create_from_cuds_object(a, session, True)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Freiburg")
            self.assertEqual(len(c.get(rel=CUBA.RELATIONSHIP)), 1)
            self.assertEqual(c._neighbours[CITY.HAS_INHABITANT],
                             {y.uid: CITY.CITIZEN})
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid, y.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(session._updated, {c.uid: c})

    def test_check_arguments(self):
        """ Test checking of arguments """
        check_arguments(str, "hello", "bye")
        check_arguments((int, float), 1, 1.2, 5.9, 2)
        check_arguments(Cuds, CITY.CITY(name="Freiburg"))
        self.assertRaises(TypeError, check_arguments, str, 12)
        self.assertRaises(TypeError, check_arguments, (int, float), 1.2, "h")
        self.assertRaises(TypeError, check_arguments,
                          Cuds, CITY.CITY)

    def test_format_class_name(self):
        """Test class name formatting"""
        self.assertEqual(format_class_name("what_is_going_on"),
                         "WhatIsGoingOn")

    def test_find_cuds_object(self):
        """ Test to find cuds objects by some criterion """
        def find_maria(x):
            return hasattr(x, "name") and x.name == "Maria"

        def find_freiburg(x):
            return hasattr(x, "name") and x.name == "Freiburg"

        def find_non_leaves(x):
            return len(x.get()) != 0

        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertIs(find_cuds_object(
            find_maria, c, CUBA.ACTIVE_RELATIONSHIP, False), p3)
        self.assertIs(find_cuds_object(
            find_maria, c, CUBA.INVERSE_OF_ACTIVE_RELATIONSHIP, False), None)
        self.assertEqual(find_cuds_object(
            find_maria, c, CUBA.INVERSE_OF_ACTIVE_RELATIONSHIP, True), list())
        all_found = find_cuds_object(
            find_maria, c, CUBA.ACTIVE_RELATIONSHIP, True)
        self.assertIs(all_found[0], p3)
        self.assertEqual(len(all_found), 1)
        self.assertIs(find_cuds_object(
            find_freiburg, c, CUBA.ACTIVE_RELATIONSHIP, False), c)
        all_found = find_cuds_object(
            find_non_leaves, c, CUBA.ACTIVE_RELATIONSHIP, True)
        self.assertEqual(len(all_found), 6)
        self.assertEqual(set(all_found), {c, p1, p2, n1, n2, s1})
        all_found = find_cuds_object(
            find_non_leaves, c, CUBA.ACTIVE_RELATIONSHIP, True,
            max_depth=1)
        self.assertEqual(len(all_found), 5)
        self.assertEqual(set(all_found), {c, p1, p2, n1, n2})

    def test_find_cuds_object_by_uid(self):
        """ Test to find a cuds object by uid in given subtree """
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertIs(find_cuds_object_by_uid(
            c.uid, c, CUBA.ACTIVE_RELATIONSHIP), c)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, c, CUBA.ACTIVE_RELATIONSHIP), p1)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, c, CUBA.ACTIVE_RELATIONSHIP), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, c, CUBA.ACTIVE_RELATIONSHIP), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, c, CUBA.ACTIVE_RELATIONSHIP), n1)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, c, CUBA.ACTIVE_RELATIONSHIP), n2)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, c, CUBA.ACTIVE_RELATIONSHIP), s1)
        self.assertIs(find_cuds_object_by_uid(
            c.uid, c, CITY.HAS_INHABITANT), c)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, c, CITY.HAS_INHABITANT), p1)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, c, CITY.HAS_INHABITANT), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, c, CITY.HAS_INHABITANT), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, c, CITY.HAS_INHABITANT), None)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, c, CITY.HAS_INHABITANT), None)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, c, CITY.HAS_INHABITANT), None)
        self.assertIs(find_cuds_object_by_uid(
            c.uid, n1, CUBA.ACTIVE_RELATIONSHIP), None)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, n1, CUBA.ACTIVE_RELATIONSHIP), None)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, n1, CUBA.ACTIVE_RELATIONSHIP), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, n1, CUBA.ACTIVE_RELATIONSHIP), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, n1, CUBA.ACTIVE_RELATIONSHIP), n1)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, n1, CUBA.ACTIVE_RELATIONSHIP), None)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, n1, CUBA.ACTIVE_RELATIONSHIP), s1)

    def test_find_cuds_objects_by_oclass(self):
        """ Test find by cuba key """
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(find_cuds_objects_by_oclass(
            CITY.CITY, c, CUBA.ACTIVE_RELATIONSHIP),
            [c])
        found = find_cuds_objects_by_oclass(
            CITY.CITIZEN,
            c, CUBA.ACTIVE_RELATIONSHIP)
        self.assertEqual(len(found), 3)
        self.assertEqual(set(found), {p1, p2, p3})
        found = find_cuds_objects_by_oclass(
            CITY.NEIGHBOURHOOD, c,
            CUBA.ACTIVE_RELATIONSHIP)
        self.assertEqual(set(found), {n1, n2})
        self.assertEqual(len(found), 2)
        self.assertEqual(find_cuds_objects_by_oclass(
            CITY.STREET, c, CUBA.ACTIVE_RELATIONSHIP),
            [s1])

    def test_find_cuds_objects_by_attribute(self):
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(
            find_cuds_objects_by_attribute("name", "Maria", c,
                                           CUBA.RELATIONSHIP), [p3]
        )
        found = find_cuds_objects_by_attribute("age", 25, c,
                                               CUBA.RELATIONSHIP)
        self.assertEqual(len(found), 3)
        self.assertEqual(set(found), {p1, p2, p3})
        found = find_cuds_objects_by_attribute(
            "age", 25, c, CUBA.INVERSE_OF_ACTIVE_RELATIONSHIP
        )
        self.assertEqual(found, [])

    def test_find_relationships(self):
        """Test find by relationships"""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        found = find_relationships(CITY.IS_INHABITANT_OF, c,
                                   CUBA.RELATIONSHIP, False)
        self.assertEqual(set(found), {p1, p2, p3})
        self.assertEqual(len(found), 3)
        found = find_relationships(CITY.IS_PART_OF, c,
                                   CUBA.RELATIONSHIP, True)
        self.assertEqual(set(found), {p3, n1, n2, s1})
        self.assertEqual(len(found), 4)
        found = find_relationships(CITY.IS_PART_OF, c,
                                   CUBA.RELATIONSHIP, False)
        self.assertEqual(set(found), {n1, n2, s1})

    def test_remove_cuds_object(self):
        """Test removeing cuds from datastructure"""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        remove_cuds_object(p3)
        self.assertEqual(p3.get(rel=CUBA.RELATIONSHIP), [])
        self.assertNotIn(p3, c.get(rel=CUBA.RELATIONSHIP))
        self.assertNotIn(p3, p1.get(rel=CUBA.RELATIONSHIP))
        self.assertNotIn(p3, p2.get(rel=CUBA.RELATIONSHIP))
        self.assertNotIn(p3, n1.get(rel=CUBA.RELATIONSHIP))
        self.assertNotIn(p3, n2.get(rel=CUBA.RELATIONSHIP))
        self.assertNotIn(p3, s1.get(rel=CUBA.RELATIONSHIP))

    def test_get_relationships_between(self):
        """ Test get the relationship between two cuds entities"""
        c = CITY.CITY(name="Freiburg")
        p = CITY.CITIZEN(name="Peter")
        self.assertEqual(get_relationships_between(c, p), set())
        self.assertEqual(get_relationships_between(p, c), set())
        c.add(p, rel=CITY.HAS_INHABITANT)
        self.assertEqual(get_relationships_between(c, p),
                         {CITY.HAS_INHABITANT})
        self.assertEqual(get_relationships_between(p, c),
                         {CITY.IS_INHABITANT_OF})
        c.add(p, rel=CITY.HAS_WORKER)
        self.assertEqual(get_relationships_between(c, p),
                         {CITY.HAS_INHABITANT,
                          CITY.HAS_WORKER})
        self.assertEqual(get_relationships_between(p, c),
                         {CITY.IS_INHABITANT_OF,
                          CITY.WORKS_IN})

    def test_get_neighbour_diff(self):
        """Check if get_neighbour_diff can compute the difference
        of neighbours between to objects.
        """
        c1 = CITY.CITY(name="Paris")
        c2 = CITY.CITY(name="Berlin")
        c3 = CITY.CITY(name="London")
        n1 = CITY.NEIGHBOURHOOD(name="Zähringen")
        n2 = CITY.NEIGHBOURHOOD(name="Herdern")
        s1 = CITY.STREET(name="Waldkircher Straße")
        s2 = CITY.STREET(name="Habsburger Straße")
        s3 = CITY.STREET(name="Lange Straße")

        n1.add(c1, c2, rel=CITY.IS_PART_OF)
        n2.add(c2, c3, rel=CITY.IS_PART_OF)
        n1.add(s1, s2)
        n2.add(s2, s3)

        self.assertEqual(
            set(get_neighbour_diff(n1, n2)),
            {(c1.uid, CITY.IS_PART_OF), (s1.uid, CITY.HAS_PART)}
        )

        self.assertEqual(
            set(get_neighbour_diff(n2, n1)),
            {(c3.uid, CITY.IS_PART_OF), (s3.uid, CITY.HAS_PART)}
        )

        self.assertEqual(
            set(get_neighbour_diff(n1, None)),
            {(c1.uid, CITY.IS_PART_OF), (s1.uid, CITY.HAS_PART),
             (c2.uid, CITY.IS_PART_OF), (s2.uid, CITY.HAS_PART)}
        )

        self.assertEqual(
            set(get_neighbour_diff(None, n2)),
            set()
        )

    def test_pretty_print(self):
        """Test printing cuds objects in a human readable way."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        f = io.StringIO()
        pretty_print(c, file=f)
        self.maxDiff = 5000
        self.assertEqual(f.getvalue(), "\n".join([
            "- Cuds object named <Freiburg>:",
            "  uuid: %s" % c.uid,
            "  type: CITY.CITY",
            "  superclasses: CITY.CITY, CITY.POPULATED_PLACE, "
            + "CITY.GEOGRAPHICAL_PLACE, CUBA.ENTITY",
            "  values: coordinates: [1 2]",
            "  description: ",
            "    To Be Determined",
            "",
            "   |_Relationship CITY.HAS_INHABITANT:",
            "   | -  CITY.CITIZEN cuds object named <Rainer>:",
            "   | .  uuid: %s" % p1.uid,
            "   | .  age: 25",
            "   | .   |_Relationship CITY.HAS_CHILD:",
            "   | .     -  CITY.CITIZEN cuds object named <Maria>:",
            "   | .        uuid: %s" % p3.uid,
            "   | .        age: 25",
            "   | -  CITY.CITIZEN cuds object named <Carlos>:",
            "   | .  uuid: %s" % p2.uid,
            "   | .  age: 25",
            "   | .   |_Relationship CITY.HAS_CHILD:",
            "   | .     -  CITY.CITIZEN cuds object named <Maria>:",
            "   | .        uuid: %s" % p3.uid,
            "   | .        (already printed)",
            "   | -  CITY.CITIZEN cuds object named <Maria>:",
            "   |    uuid: %s" % p3.uid,
            "   |    (already printed)",
            "   |_Relationship CITY.HAS_PART:",
            "     -  CITY.NEIGHBOURHOOD cuds object named <Zähringen>:",
            "     .  uuid: %s" % n1.uid,
            "     .  coordinates: [2 3]",
            "     .   |_Relationship CITY.HAS_PART:",
            "     .     -  CITY.STREET cuds object named <Lange Straße>:",
            "     .        uuid: %s" % s1.uid,
            "     .        coordinates: [4 5]",
            "     .         |_Relationship CITY.HAS_INHABITANT:",
            "     .           -  CITY.CITIZEN cuds object named <Carlos>:",
            "     .           .  uuid: %s" % p2.uid,
            "     .           .  (already printed)",
            "     .           -  CITY.CITIZEN cuds object named <Maria>:",
            "     .              uuid: %s" % p3.uid,
            "     .              (already printed)",
            "     -  CITY.NEIGHBOURHOOD cuds object named <St. Georgen>:",
            "        uuid: %s" % n2.uid,
            "        coordinates: [3 4]",
            "         |_Relationship CITY.HAS_PART:",
            "           -  CITY.STREET cuds object named <Lange Straße>:",
            "              uuid: %s" % s1.uid,
            "              (already printed)",
            ""]))
