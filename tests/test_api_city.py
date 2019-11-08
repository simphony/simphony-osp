# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import uuid

from osp.core.utils import clone_cuds_object, create_from_cuds_object, \
    get_neighbour_diff
from osp.core.session.core_session import CoreSession
from osp.core.cuds import Cuds
from osp.core import CITY, CUBA


class TestAPICity(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        self.assertRaises(TypeError, CITY.CITY, name="name",
                          coordinates=[1, 2], uid=0, unwanted="unwanted")
        self.assertRaises(TypeError, CITY.CITY)

        c = CITY.CITY(name="a city")
        p = CITY.PERSON()
        self.assertEqual(c.is_a, CITY.CITY)
        self.assertEqual(p.is_a, CITY.PERSON)

    def test_uid(self):
        """
        Tests that the uid variable contains a UUID object
        """
        c = CITY.CITY(name="a city")
        self.assertIsInstance(c.uid, uuid.UUID)

    def test_set_throws_exception(self):
        """
        Tests that setting a value for a key not in restricted
        keys throws an exception.
        """
        c = CITY.CITY(name="a city")
        self.assertRaises(ValueError, c._neighbours.__setitem__,
                          "not an allowed key", 15)

    def test_add(self):
        """
        Tests the standard, normal behaviour of the add() method
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neighbourhood")
        p = CITY.CITIZEN()

        c.add(n)
        self.assertEqual(c.get(n.uid).uid, n.uid)

        # Test the inverse relationship
        get_inverse = n.get(rel=CITY.IS_PART_OF)
        self.assertEqual(get_inverse, [c])

        c.add(p, rel=CITY.HAS_INHABITANT)
        self.assertEqual(c.get(p.uid).uid, p.uid)

    def test_add_throws_exception(self):
        """
        Tests the add() method for unusual behaviours.

         - Adding an object that is already there
         - Adding an unsupported object
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")

        c.add(n)
        self.assertRaises(ValueError, c.add, n)
        self.assertRaises(TypeError, c.add, "Not a CUDS objects")

    def test_recursive_add(self):
        """Tests if add() works correctly if added cuds_object is from another session.
        """
        c = CITY.CITY(name="City")
        p1 = CITY.CITIZEN()
        c.add(p1, rel=CITY.HAS_INHABITANT)

        second_session = CoreSession()
        w = CITY.CITY_WRAPPER(session=second_session)
        cw = w.add(c)
        p1w = cw.get(p1.uid)
        self.assertIs(cw.session, second_session)
        self.assertIs(p1w.session, second_session)
        self.assertIsNot(c.session, second_session)
        self.assertIsNot(p1.session, second_session)

        p2 = CITY.CITIZEN()
        p3 = CITY.CITIZEN()
        p4 = CITY.CITIZEN()
        c.add(p2, p3, rel=CITY.HAS_INHABITANT)
        p1.add(p2, rel=CITY.HAS_CHILD)
        p3.add(p2, rel=CITY.HAS_CHILD)
        p2.add(p4, rel=CITY.HAS_CHILD)

        cw.add(p2, rel=CITY.HAS_INHABITANT)
        p2w = cw.get(p2.uid)
        p4w = p2w.get(p4.uid)

        # check if there are unexpected changes in the first session
        # first check active relationships
        self.assertEqual(set(c._neighbours[CITY.HAS_INHABITANT].keys()),
                         set([p1.uid, p2.uid, p3.uid]))
        self.assertEqual(set([p2.uid]),
                         set(p1._neighbours[CITY.HAS_CHILD].keys()))
        self.assertEqual(set([p2.uid]),
                         set(p3._neighbours[CITY.HAS_CHILD].keys()))
        self.assertEqual(set([p4.uid]), set(
            p2._neighbours[CITY.HAS_CHILD].keys()))

        # check passive relationships
        self.assertEqual(set([c.uid]),
                         set(p1._neighbours[CITY.IS_INHABITANT_OF].keys()))
        self.assertEqual(set([p1.uid, p3.uid]),
                         set(p2._neighbours[CITY.IS_CHILD_OF].keys()))
        self.assertEqual(set([c.uid]),
                         set(p2._neighbours[CITY.IS_INHABITANT_OF].keys()))
        self.assertEqual(set([c.uid]),
                         set(p3._neighbours[CITY.IS_INHABITANT_OF].keys()))
        self.assertEqual(set([p2.uid]),
                         set(p4._neighbours[CITY.IS_CHILD_OF].keys()))

        # check if items correctly added in second session
        # active relations
        self.assertEqual(set(cw._neighbours[CITY.HAS_INHABITANT].keys()),
                         set([p1w.uid, p2w.uid]))
        self.assertEqual(set([p2w.uid]),
                         set(p1w._neighbours[CITY.HAS_CHILD].keys()))
        self.assertEqual(set([p4w.uid]),
                         set(p2w._neighbours[CITY.HAS_CHILD].keys()))

        # passive relations
        self.assertEqual(set([cw.uid]),
                         set(p1w._neighbours[CITY.IS_INHABITANT_OF].keys()))
        self.assertEqual(set([p1w.uid]),
                         set(p2w._neighbours[CITY.IS_CHILD_OF].keys()))
        self.assertEqual(set([cw.uid]),
                         set(p2w._neighbours[CITY.IS_INHABITANT_OF].keys()))
        self.assertEqual(set([p2w.uid]),
                         set(p4w._neighbours[CITY.IS_CHILD_OF].keys()))

    def test_fix_neighbours(self):
        w1 = CITY.CITY_WRAPPER(session=CoreSession())
        w2 = CITY.CITY_WRAPPER(session=CoreSession())

        c1w1 = CITY.CITY(name="city1")  # parent in both wrappers
        c2w1 = CITY.CITY(name="city2")  # parent in w1, not present in w2
        c3w1 = CITY.CITY(name="city3")  # parent only in w1, present in w2
        c4w1 = CITY.CITY(name="city4")  # parent only in w2
        p1w1 = CITY.CITIZEN(name="citizen")
        p2w1 = CITY.CITIZEN(name="child")

        w2.add(c1w1, c3w1, c4w1)
        c1w2, c3w2, c4w2 = w2.get(c1w1.uid, c3w1.uid, c4w1.uid)
        c1w2.add(p1w1, rel=CITY.HAS_INHABITANT)
        c4w2.add(p1w1, rel=CITY.HAS_INHABITANT)
        p1w2 = c1w2.get(p1w1.uid)
        p1w2.add(p2w1, rel=CITY.HAS_CHILD)
        p2w2 = p1w2.get(p2w1.uid)

        w1.add(c1w1, c2w1, c3w1, c4w1)
        c1w1.add(p1w1, rel=CITY.HAS_INHABITANT)
        c2w1.add(p1w1, rel=CITY.HAS_INHABITANT)
        c3w1.add(p1w1, rel=CITY.HAS_INHABITANT)

        self.assertEqual(
            set(p1w1._neighbours[CITY.IS_INHABITANT_OF].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid]))
        self.assertEqual(
            set(p2w2._neighbours[CITY.IS_CHILD_OF].keys()),
            set([p1w2.uid]))

        missing = dict()
        Cuds._fix_neighbours(new_cuds_object=p1w1,
                             old_cuds_object=p1w2,
                             session=p1w2.session,
                             missing=missing)

        # check if connections cuds_objects that are no
        # longer parents are in the missing dict
        self.assertIn(c2w1.uid, missing)
        self.assertEqual(
            set(p1w1._neighbours[CITY.IS_INHABITANT_OF].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid, c4w1.uid]))
        self.assertNotIn(CITY.IS_PART_OF, p2w2._neighbours)

        # check if there are no unexpected other changes
        self.assertEqual(
            set(c1w1._neighbours[CITY.HAS_INHABITANT].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c2w1._neighbours[CITY.HAS_INHABITANT].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w1._neighbours[CITY.HAS_INHABITANT].keys()),
            set([p1w1.uid]))
        self.assertNotIn(CITY.HAS_INHABITANT, c4w1._neighbours)

        # check if the parents in w2 have been updated
        self.assertEqual(
            set(c1w2._neighbours[CITY.HAS_INHABITANT].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w2._neighbours[CITY.HAS_INHABITANT].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c4w2._neighbours[CITY.HAS_INHABITANT].keys()),
            set([p1w1.uid]))

    def test_get(self):
        """
        Tests the standard, normal behaviour of the get() method.

         - get()
         - get(*uids)
         - get(rel)
         - get(oclass)
         - get(*uids, rel)
         - get(rel, oclass)
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")
        p = CITY.CITIZEN(name="John Smith")
        q = CITY.CITIZEN(name="Jane Doe")
        c.add(n)
        c.add(p, q, rel=CITY.HAS_INHABITANT)

        # get()
        get_default = c.get()
        self.assertEqual(set(get_default), {n, p, q})

        # get(*uids)
        get_p_uid = c.get(p.uid)
        self.assertEqual(get_p_uid, p)
        get_q_uid = c.get(q.uid)
        self.assertEqual(get_q_uid, q)
        get_nq_uid = c.get(n.uid, q.uid)
        self.assertEqual(set(get_nq_uid), {n, q})
        get_new_uid = c.get(uuid.uuid4())
        self.assertEqual(get_new_uid, None)

        # get(rel)
        get_has_part = c.get(rel=CITY.HAS_INHABITANT)
        self.assertEqual(set(get_has_part), {p, q})
        get_encloses = c.get(rel=CITY.ENCLOSES)
        self.assertEqual(set(get_encloses), {n, p, q})
        get_inhabits = c.get(rel=CITY.IS_INHABITANT_OF)
        self.assertEqual(get_inhabits, [])

        # get(oclass)
        get_citizen = c.get(oclass=CITY.CITIZEN)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(oclass=CITY.BUILDING)
        self.assertEqual(get_building, [])
        get_citizen = c.get(oclass=CITY.PERSON)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(
            oclass=CITY.ARCHITECTURAL_STRUCTURE)
        self.assertEqual(get_building, [])

        # get(*uids, rel)
        get_has_part_p = c.get(p.uid, rel=CITY.HAS_INHABITANT)
        self.assertEqual(get_has_part_p, p)

        get_has_part_q = c.get(q.uid, rel=CITY.HAS_PART)
        self.assertEqual(get_has_part_q, None)

        # get(rel, oclass)
        get_inhabited_citizen = c.get(rel=CITY.HAS_INHABITANT,
                                      oclass=CITY.CITIZEN)
        self.assertEqual(set(get_inhabited_citizen), {p, q})

    def test_get_throws_exception(self):
        """
        Tests the get() method for unusual behaviours.

         - Getting with a wrong type
         - Getting with a not allowed combination of arguments
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")
        c.add(n)

        self.assertRaises(TypeError, c.get, "not a proper key")
        self.assertRaises(TypeError, c.get,
                          n.uid,
                          oclass=CITY.NEIGHBOURHOOD)

    def test_update(self):
        """
        Tests the standard, normal behaviour of the update() method.
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")
        new_n = create_from_cuds_object(n, CoreSession(), True)
        new_s = CITY.STREET(name="a new street")
        new_n.add(new_s)
        c.add(n)

        old_neighbourhood = c.get(n.uid)
        old_streets = old_neighbourhood.get(
            oclass=CITY.STREET)
        self.assertEqual(old_streets, [])

        c.update(new_n)

        new_neighbourhood = c.get(n.uid)
        self.assertIs(new_neighbourhood, n)
        new_streets = new_neighbourhood.get(
            oclass=CITY.STREET)
        self.assertEqual(new_streets, [new_s])

    def test_remove(self):
        """
        Tests the standard, normal behaviour of the remove() method.

         - remove()
         - remove(*uids/DataContainers)
         - remove(rel)
         - remove(oclass)
         - remove(rel, oclass)
         - remove(*uids/DataContainers, rel)
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")
        p = CITY.CITIZEN(name="John Smith")
        q = CITY.CITIZEN(name="Jane Doe")
        c.add(n)
        c.add(q, p, rel=CITY.HAS_INHABITANT)

        self.assertIn(CITY.HAS_PART, c._neighbours)
        self.assertIn(CITY.HAS_INHABITANT, c._neighbours)

        # remove()
        c.remove()
        self.assertFalse(c._neighbours)
        # inverse
        get_inverse = p.get(rel=CITY.IS_PART_OF)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers)
        c.add(n)
        c.add(p, q, rel=CITY.HAS_INHABITANT)
        get_all = c.get()
        self.assertIn(p, get_all)
        c.remove(p.uid)
        get_all = c.get()
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=CITY.IS_PART_OF)
        self.assertEqual(get_inverse, [])

        # remove(rel)
        c.remove(rel=CITY.HAS_PART)
        self.assertNotIn(CITY.HAS_PART, c._neighbours)
        # inverse
        get_inverse = n.get(rel=CITY.IS_PART_OF)
        self.assertEqual(get_inverse, [])

        # remove(oclass)
        c.remove(oclass=CITY.CITIZEN)
        self.assertNotIn(q, c.get())
        # inverse
        get_inverse = q.get(rel=CITY.IS_INHABITANT_OF)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers, rel)
        c.add(p, q, rel=CITY.HAS_INHABITANT)
        self.assertIn(CITY.HAS_INHABITANT, c._neighbours)
        c.remove(q, p, rel=CITY.HAS_INHABITANT)
        self.assertNotIn(CITY.HAS_INHABITANT, c._neighbours)
        # inverse
        get_inverse = p.get(rel=CITY.IS_INHABITANT_OF)
        self.assertEqual(get_inverse, [])

        # remove(rel, oclass)
        c.add(p, rel=CITY.HAS_INHABITANT)
        c.add(n)
        c.remove(rel=CITY.HAS_INHABITANT,
                 oclass=CITY.CITIZEN)
        get_all = c.get()
        self.assertIn(n, get_all)
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=CITY.IS_INHABITANT_OF)
        self.assertEqual(get_inverse, [])

    def test_remove_throws_exception(self):
        """
        Tests the remove() method for unusual behaviours.

         - Removing with a wrong key
         - Removing something non-existent
         - Removing with a not allowed argument combination
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")

        # Wrong key
        self.assertRaises(TypeError, c.remove, "not a proper key")

        # Non-existent
        self.assertRaises(RuntimeError, c.remove, n.uid)
        self.assertRaises(RuntimeError, c.remove, rel=CITY.HAS_PART)
        self.assertRaises(RuntimeError, c.remove,
                          oclass=CITY.STREET)
        self.assertRaises(
            RuntimeError, c.remove, n.uid, rel=CITY.HAS_PART)

        # Wrong arguments
        self.assertRaises(TypeError, c.remove, n.uid,
                          oclass=CITY.STREET)

    def test_update_throws_exception(self):
        """
        Tests the update() method for unusual behaviours.

         - Update an element that wasn't added before
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")
        c.add(n)
        p = CITY.CITIZEN()
        self.assertRaises(ValueError, c.update, p)

    def test_iter(self):
        """
        Tests the iter() method when no cuba key is provided.
        """
        c = CITY.CITY(name="a city")
        n = CITY.NEIGHBOURHOOD(name="a neigbourhood")
        p = CITY.CITIZEN(name="John Smith")
        q = CITY.CITIZEN(name="Jane Doe")
        c.add(n)
        c.add(p, q, rel=CITY.HAS_INHABITANT)

        elements = set(list(c.iter()))
        self.assertEqual(elements, {n, p, q})

    # def test_check_valid_add(self):  # TODO
    #     """Check if _check_valid_add throws exceptions when illegal
    #     relationships are added.
    #     """
    #     c = cuds.classes.PopulatedPlace("Freiburg")
    #     p1 = cuds.classes.Person(name="Peter")
    #     c.add(p1, rel=cuds.classes.HasWorker)
    #     p2 = CITY.CITIZEN(name="Martin")
    #     c.add(p2, rel=cuds.classes.HasWorker)
    #     p3 = cuds.classes.LivingBeing(name="Mimi")
    #     self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)
    #     c.remove()

    #     c.add(p1, rel=cuds.classes.HasMajor)
    #     c.add(p2, rel=cuds.classes.HasMajor)
    #     self.assertRaises(ValueError, c.add, p1, rel=CITY.HAS_PART)

    #     c = CITY.CITY("Freiburg")
    #     c.add(p1, rel=cuds.classes.HasWorker)
    #     c.add(p2, rel=cuds.classes.HasWorker)
    #     self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)

    #     c = cuds.classes.GeographicalPlace("Freiburg")
    #     self.assertRaises(ValueError, c.add, p1, rel=cuds.classes.HasWorker)
    #     self.assertRaises(ValueError, c.add, p2, rel=cuds.classes.HasWorker)
    #     self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)

    #     Cuds.CUDS_SETTINGS["check_relationship_supported"] = False
    #     c.add(p1, rel=cuds.classes.HasWorker)
    #     c.add(p2, rel=cuds.classes.HasWorker)
    #     c.add(p3, rel=cuds.classes.HasWorker)
    #     Cuds.CUDS_SETTINGS["check_relationship_supported"] = True

    def test_recursive_store(self):
        """Check if _recursive_store correctly stores cuds_objects recursively,
        correcting dangling and one-way connections.
        """
        c = CITY.CITY(name="Freiburg")
        with CoreSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            cw = w.add(c)

            p1 = CITY.CITIZEN()
            p2 = CITY.CITIZEN()
            p3 = CITY.CITIZEN()
            p4 = CITY.CITIZEN()
            c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
            p3.add(p1, p2, rel=CITY.IS_CHILD_OF)
            p3.add(p4, rel=CITY.HAS_CHILD)

            cw = w._recursive_store(c, cw)

            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            p4w = p3w.get(p4.uid)

            self.assertEqual(w.get(rel=CITY.HAS_PART), [cw])
            self.assertEqual(
                set(cw.get(rel=CITY.HAS_INHABITANT)),
                {p1w, p2w, p3w}
            )
            self.assertEqual(
                set(cw.get(rel=CITY.IS_PART_OF)),
                {w}
            )

            self.assertEqual(p3w.get(rel=CITY.IS_INHABITANT_OF), [cw])
            self.assertEqual(
                set(p3w.get(rel=CITY.IS_CHILD_OF)),
                {p1w, p2w}
            )
            self.assertEqual(p3w.get(rel=CITY.HAS_CHILD), [p4w])

    def test_fix_new_parents(self):
        """Check that _fix_new_parent:
        - Deletes connection to new parents not available in new session
        - Adds connection to new parents available in new session
        """
        n = CITY.NEIGHBOURHOOD(name="Zähringen")
        # parent in both sessions
        c1 = CITY.CITY(name="Berlin")
        # only parent in default session (available in both)
        c2 = CITY.CITY(name="Paris")
        n.add(c1, c2, rel=CITY.IS_PART_OF)

        with CoreSession() as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            c1w, c2w = wrapper.add(c1, c2)
            nw = c2w.get(n.uid)
            nw.remove(c2.uid, rel=CUBA.RELATIONSHIP)

            # only parent + available in default session
            c3 = CITY.CITY(name="London")
            n.add(c3, rel=CITY.IS_PART_OF)

            n = clone_cuds_object(n)
            n._session = session
            new_parent_diff = get_neighbour_diff(
                n, nw, mode="non-active")
            new_parents = session.load(*[x[0] for x in new_parent_diff])

            missing = dict()
            Cuds._fix_new_parents(new_cuds_object=n,
                                  new_parents=new_parents,
                                  new_parent_diff=new_parent_diff,
                                  missing=missing)

        self.assertEqual(
            set(n.get(rel=CITY.IS_PART_OF)),
            {c1w, c2w, None}  # missing parent, should be in missing dict
        )
        self.assertEqual(missing, {c3.uid: [(n, CITY.IS_PART_OF)]})
        self.assertEqual(c2w.get(rel=CITY.HAS_PART), [n])

    def test_fix_old_neighbours(self):
        """Check if _fix_old_neighbours.
        - Deletes old children.
        - Adds connection to old parents.
        """
        c = CITY.CITY(name="Freiburg")

        with CoreSession() as session:
            wrapper = CITY.CITY_WRAPPER(session=session)
            cw = wrapper.add(c)
            n = CITY.NEIGHBOURHOOD(name="Zähringen")
            nw = cw.add(n)

            c = clone_cuds_object(c)
            c._session = session
            old_neighbour_diff = get_neighbour_diff(cw, c)
            old_neighbours = session.load(*[x[0] for x in old_neighbour_diff])
            Cuds._fix_old_neighbours(new_cuds_object=c,
                                     old_cuds_object=cw,
                                     old_neighbours=old_neighbours,
                                     old_neighbour_diff=old_neighbour_diff)
        self.assertEqual(c.get(rel=CITY.IS_PART_OF), [wrapper])
        self.assertEqual(c.get(rel=CITY.HAS_PART), [])
        self.assertEqual(nw.get(rel=CITY.IS_PART_OF), [])
        self.assertEqual(wrapper.get(rel=CITY.HAS_PART), [c])

    def test_add_twice(self):
        """ Test what happens if you add the same
        object twice to a new session"""
        p = CITY.CITIZEN(name="Ralf")
        c1 = CITY.CITY(name="Freiburg")
        c2 = CITY.CITY(name="Offenburg")
        with CoreSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            c1w, c2w = w.add(c1, c2)
            pw1 = c1w.add(p, rel=CITY.HAS_INHABITANT)
            pw2 = c2w.add(p, rel=CITY.HAS_INHABITANT)
            self.assertIs(pw1, pw2)
            self.assertEqual(set(pw1.get(rel=CITY.IS_INHABITANT_OF)),
                             {c1w, c2w})


if __name__ == '__main__':
    unittest.main()
