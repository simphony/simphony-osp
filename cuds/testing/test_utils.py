# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import io
import unittest
import cuds.classes
from cuds.classes.core.session.core_session import CoreSession
from cuds.utils import (destroy_cuds_object, clone_cuds_object,
                        create_for_session, create_from_cuds_object,
                        check_arguments, format_class_name, find_cuds_object,
                        find_cuds_object_by_uid, remove_cuds_object,
                        get_ancestors, pretty_print, find_cuds_objects_by_cuba_key)


class TestUtils(unittest.TestCase):

    def test_destroy_cuds_object(self):
        """Test destroyion of cuds"""
        a = cuds.classes.City("Freiburg")
        b = cuds.classes.Citizen(age=12, name="Horst")
        with CoreSession() as session:
            w = cuds.classes.CityWrapper(session=session)
            aw = w.add(a)
            bw = aw.add(b, rel=cuds.classes.HasInhabitant)
            session._expired = {bw.uid}
            destroy_cuds_object(aw)

            self.assertEqual(a.name, "Freiburg")
            self.assertEqual(bw.name, "Horst")
            self.assertEqual(aw.name, None)
            self.assertEqual(aw.get(), [])

            destroy_cuds_object(bw)
            self.assertEqual(bw.name, None)
            self.assertEqual(session._expired, set())

    def test_clone_cuds_object(self):
        """Test cloning of cuds"""
        a = cuds.classes.City("Freiburg")
        with CoreSession() as session:
            w = cuds.classes.CityWrapper(session=session)
            aw = w.add(a)
            clone = clone_cuds_object(aw)
            self.assertIsNot(aw, None)
            self.assertIs(clone.session, aw.session)
            self.assertEqual(clone.uid, aw.uid)
            self.assertIs(aw, session._registry.get(aw.uid))
            self.assertEqual(clone.name, "Freiburg")

    def test_create_for_session(self):
        """Test creation of cuds_objects for different session"""
        default_session = CoreSession()
        cuds.classes.Cuds._session = default_session
        a = cuds.classes.City("Freiburg")
        self.assertIs(a.session, default_session)
        with CoreSession() as session:
            b = create_for_session(cuds.classes.City,
                                   {"name": "Offenburg", "uid": a.uid},
                                   session=session)
            self.assertEqual(b.name, "Offenburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid})
            self.assertIs(session._registry.get(b.uid), b)

            x = cuds.classes.Citizen()
            b.add(x, rel=cuds.classes.HasInhabitant)

            c = create_for_session(cuds.classes.City,
                                   {"name": "Emmendingen", "uid": a.uid},
                                   session=session)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Emmendingen")
            self.assertEqual(c.get(rel=cuds.classes.Relationship), [])
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid})
            self.assertIs(default_session._registry.get(a.uid), a)

    def test_create_from_cuds_object(self):
        """Test copying cuds_objects to different session"""
        default_session = CoreSession()
        cuds.classes.Cuds._session = default_session
        default_session = CoreSession()
        cuds.classes.Cuds._session = default_session
        a = cuds.classes.City("Freiburg")
        self.assertIs(a.session, default_session)
        with CoreSession() as session:
            b = create_from_cuds_object(a, session)
            self.assertEqual(b.name, "Freiburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid})
            self.assertIs(session._registry.get(b.uid), b)

            b.name = "Emmendingen"
            x = cuds.classes.Citizen(age=54, name="Franz")
            b.add(x, rel=cuds.classes.HasInhabitant)
            y = cuds.classes.Citizen(age=21, name="Rolf")
            a.add(y, rel=cuds.classes.HasInhabitant)

            c = create_from_cuds_object(a, session)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Freiburg")
            self.assertEqual(len(c.get(rel=cuds.classes.Relationship)), 1)
            self.assertEqual(c[cuds.classes.HasInhabitant],
                             {y.uid: cuds.classes.Citizen.cuba_key})
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid, y.uid})
            self.assertIs(default_session._registry.get(a.uid), a)

    def test_check_arguments(self):
        """ Test checking of arguments """
        check_arguments(str, "hello", "bye")
        check_arguments((int, float), 1, 1.2, 5.9, 2)
        check_arguments(cuds.classes.Cuds, cuds.classes.City("Freiburg"))
        self.assertRaises(TypeError, check_arguments, str, 12)
        self.assertRaises(TypeError, check_arguments, (int, float), 1.2, "h")
        self.assertRaises(TypeError, check_arguments,
                          cuds.classes.Cuds, cuds.classes.City)

    def test_format_class_name(self):
        """Test class name formatting"""
        self.assertEqual(format_class_name("what_is_going_on"),
                         "WhatIsGoingOn")

    def get_test_city(self):
        """helper function"""
        c = cuds.classes.City("Freiburg")
        p1 = cuds.classes.Citizen(name="Rainer")
        p2 = cuds.classes.Citizen(name="Carlos")
        p3 = cuds.classes.Citizen(name="Maria")
        n1 = cuds.classes.Neighbourhood("Zähringen")
        n2 = cuds.classes.Neighbourhood("St. Georgen")
        s1 = cuds.classes.Street("Lange Straße")

        c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p3, rel=cuds.classes.HasChild)
        p2.add(p3, rel=cuds.classes.HasChild)
        c.add(n1, n2)
        n1.add(s1)
        n2.add(s1)
        s1.add(p2, p3, rel=cuds.classes.HasInhabitant)
        return [c, p1, p2, p3, n1, n2, s1]

    def test_find_cuds_object(self):
        """ Test to find cuds objects by some criterion """
        def find_maria(x):
            return hasattr(x, "name") and x.name == "Maria"

        def find_freiburg(x):
            return hasattr(x, "name") and x.name == "Freiburg"

        def find_leaves(x):
            return len(x.get()) != 0

        c, p1, p2, p3, n1, n2, s1 = self.get_test_city()
        self.assertIs(find_cuds_object(
            find_maria, c, cuds.classes.ActiveRelationship, False), p3)
        self.assertIs(find_cuds_object(
            find_maria, c, cuds.classes.PassiveRelationship, False), None)
        self.assertEquals(find_cuds_object(
            find_maria, c, cuds.classes.PassiveRelationship, True), list())
        all_found = find_cuds_object(
            find_maria, c, cuds.classes.ActiveRelationship, True)
        self.assertIs(all_found[0], p3)
        self.assertEquals(len(all_found), 1)
        self.assertIs(find_cuds_object(
            find_freiburg, c, cuds.classes.ActiveRelationship, False), c)
        all_found = find_cuds_object(
            find_leaves, c, cuds.classes.ActiveRelationship, True)
        self.assertEquals(len(all_found), 6)
        self.assertEquals(set(all_found), {c, p1, p2, n1, n2, s1})

    def test_find_cuds_object_by_uid(self):
        """ Test to find a cuds object by uid in given subtree """
        c, p1, p2, p3, n1, n2, s1 = self.get_test_city()
        self.assertIs(find_cuds_object_by_uid(
            c.uid, c, cuds.classes.ActiveRelationship), c)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, c, cuds.classes.ActiveRelationship), p1)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, c, cuds.classes.ActiveRelationship), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, c, cuds.classes.ActiveRelationship), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, c, cuds.classes.ActiveRelationship), n1)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, c, cuds.classes.ActiveRelationship), n2)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, c, cuds.classes.ActiveRelationship), s1)
        self.assertIs(find_cuds_object_by_uid(
            c.uid, c, cuds.classes.HasInhabitant), c)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, c, cuds.classes.HasInhabitant), p1)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, c, cuds.classes.HasInhabitant), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, c, cuds.classes.HasInhabitant), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, c, cuds.classes.HasInhabitant), None)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, c, cuds.classes.HasInhabitant), None)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, c, cuds.classes.HasInhabitant), None)
        self.assertIs(find_cuds_object_by_uid(
            c.uid, n1, cuds.classes.ActiveRelationship), None)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, n1, cuds.classes.ActiveRelationship), None)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, n1, cuds.classes.ActiveRelationship), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, n1, cuds.classes.ActiveRelationship), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, n1, cuds.classes.ActiveRelationship), n1)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, n1, cuds.classes.ActiveRelationship), None)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, n1, cuds.classes.ActiveRelationship), s1)

    def test_find_cuds_objects_by_cuba_key(self):
        """ Test find by cuba key """
        c, p1, p2, p3, n1, n2, s1 = self.get_test_city()
        self.assertEquals(find_cuds_objects_by_cuba_key(
            cuds.classes.City.cuba_key, c, cuds.classes.ActiveRelationship),
            [c])
        found = find_cuds_objects_by_cuba_key(
            cuds.classes.Citizen.cuba_key,
            c, cuds.classes.ActiveRelationship)
        self.assertEquals(len(found), 3)
        self.assertEquals(set(found), {p1, p2, p3})
        found = find_cuds_objects_by_cuba_key(
            cuds.classes.Neighbourhood.cuba_key, c,
            cuds.classes.ActiveRelationship)
        self.assertEquals(set(found), {n1, n2})
        self.assertEquals(len(found), 2)
        self.assertEquals(find_cuds_objects_by_cuba_key(
            cuds.classes.Street.cuba_key, c, cuds.classes.ActiveRelationship),
            [s1])

    def test_remove_cuds_object(self):
        c, p1, p2, p3, n1, n2, s1 = self.get_test_city()
        remove_cuds_object(p3)
        self.assertEqual(p3.get(rel=cuds.classes.Relationship), [])
        self.assertNotIn(p3, c.get(rel=cuds.classes.Relationship))
        self.assertNotIn(p3, p1.get(rel=cuds.classes.Relationship))
        self.assertNotIn(p3, p2.get(rel=cuds.classes.Relationship))
        self.assertNotIn(p3, n1.get(rel=cuds.classes.Relationship))
        self.assertNotIn(p3, n2.get(rel=cuds.classes.Relationship))
        self.assertNotIn(p3, s1.get(rel=cuds.classes.Relationship))

    def test_get_ancestors(self):
        ancestors = ['Person', 'LivingBeing', 'Entity', 'Cuds']
        self.assertEqual(get_ancestors(cuds.classes.Citizen), ancestors)
        self.assertEqual(get_ancestors(cuds.classes.Citizen()), ancestors)

    def test_pretty_print(self):
        c, p1, p2, p3, n1, n2, s1 = self.get_test_city()
        f = io.StringIO()
        pretty_print(c, file=f)
        self.maxDiff = 5000
        self.assertEqual(f.getvalue(), "\n".join([
            "- Cuds object named <Freiburg>:",
            "  uuid: %s" % c.uid,
            "  type: CUBA.CITY",
            "  ancestors: PopulatedPlace, GeographicalPlace, Entity, Cuds",
            "  description: ",
            "    To Be Determined",
            "    ",
            "   |_Relationship CUBA.HAS_INHABITANT:",
            "   | -  CUBA.CITIZEN cuds object named <Rainer>:",
            "   | .  uuid: %s" % p1.uid,
            "   | .  age: 25",
            "   | .   |_Relationship CUBA.HAS_CHILD:",
            "   | .     -  CUBA.CITIZEN cuds object named <Maria>:",
            "   | .        uuid: %s" % p3.uid,
            "   | .        age: 25",
            "   | -  CUBA.CITIZEN cuds object named <Carlos>:",
            "   | .  uuid: %s" % p2.uid,
            "   | .  age: 25",
            "   | .   |_Relationship CUBA.HAS_CHILD:",
            "   | .     -  CUBA.CITIZEN cuds object named <Maria>:",
            "   | .        uuid: %s" % p3.uid,
            "   | .        (already printed)",
            "   | -  CUBA.CITIZEN cuds object named <Maria>:",
            "   |    uuid: %s" % p3.uid,
            "   |    (already printed)",
            "   |_Relationship CUBA.HAS_PART:",
            "     -  CUBA.NEIGHBOURHOOD cuds object named <Zähringen>:",
            "     .  uuid: %s" % n1.uid,
            "     .   |_Relationship CUBA.HAS_PART:",
            "     .     -  CUBA.STREET cuds object named <Lange Straße>:",
            "     .        uuid: %s" % s1.uid,
            "     .         |_Relationship CUBA.HAS_INHABITANT:",
            "     .           -  CUBA.CITIZEN cuds object named <Carlos>:",
            "     .           .  uuid: %s" % p2.uid,
            "     .           .  (already printed)",
            "     .           -  CUBA.CITIZEN cuds object named <Maria>:",
            "     .              uuid: %s" % p3.uid,
            "     .              (already printed)",
            "     -  CUBA.NEIGHBOURHOOD cuds object named <St. Georgen>:",
            "        uuid: %s" % n2.uid,
            "         |_Relationship CUBA.HAS_PART:",
            "           -  CUBA.STREET cuds object named <Lange Straße>:",
            "              uuid: %s" % s1.uid,
            "              (already printed)",
            ""]))
