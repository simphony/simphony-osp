# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import uuid

from cuds.utils import clone_cuds_object, create_from_cuds_object, \
    get_neighbour_diff
from cuds.session.core_session import CoreSession
from cuds.classes.cuds import Cuds
import cuds.classes


class TestAPICity(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        self.assertRaises(TypeError,
                          cuds.classes.City, "name", [1, 2], "uid", "unwanted")

        c = cuds.classes.City("a city")
        p = cuds.classes.Person()
        self.assertIsInstance(c, cuds.classes.City)
        self.assertIsInstance(p, cuds.classes.Person)

    def test_uid(self):
        """
        Tests that the uid variable contains a UUID object
        """
        c = cuds.classes.City("a city")
        self.assertIsInstance(c.uid, uuid.UUID)

    def test_set_throws_exception(self):
        """
        Tests that setting a value for a key not in restricted
        keys throws an exception.
        """
        c = cuds.classes.City("a city")
        self.assertRaises(ValueError, c.__setitem__, "not an allowed key", 15)

    def test_add(self):
        """
        Tests the standard, normal behaviour of the add() method
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neighbourhood")
        p = cuds.classes.Citizen()

        c.add(n)
        self.assertEqual(c.get(n.uid).uid, n.uid)

        # Test the inverse relationship
        get_inverse = n.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [c])

        c.add(p, rel=cuds.classes.HasInhabitant)
        self.assertEqual(c.get(p.uid).uid, p.uid)

    def test_add_throws_exception(self):
        """
        Tests the add() method for unusual behaviours.

         - Adding an object that is already there
         - Adding an unsupported object
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")

        c.add(n)
        self.assertRaises(ValueError, c.add, n)
        self.assertRaises(TypeError, c.add, "Not a CUDS objects")

    def test_recursive_add(self):
        """Tests if add() works correctly if added cuds_object is from another session.
        """
        c = cuds.classes.City("City")
        p1 = cuds.classes.Citizen()
        c.add(p1, rel=cuds.classes.HasInhabitant)

        second_session = CoreSession()
        w = cuds.classes.CityWrapper(session=second_session)
        cw = w.add(c)
        p1w = cw.get(p1.uid)
        self.assertIs(cw.session, second_session)
        self.assertIs(p1w.session, second_session)
        self.assertIsNot(c.session, second_session)
        self.assertIsNot(p1.session, second_session)

        p2 = cuds.classes.Citizen()
        p3 = cuds.classes.Citizen()
        p4 = cuds.classes.Citizen()
        c.add(p2, p3, rel=cuds.classes.HasInhabitant)
        p1.add(p2, rel=cuds.classes.HasChild)
        p3.add(p2, rel=cuds.classes.HasChild)
        p2.add(p4, rel=cuds.classes.HasChild)

        cw.add(p2, rel=cuds.classes.HasInhabitant)
        p2w = cw.get(p2.uid)
        p4w = p2w.get(p4.uid)

        # check if there are unexpected changes in the first session
        # first check active relationships
        self.assertEqual(set(c[cuds.classes.HasInhabitant].keys()),
                         set([p1.uid, p2.uid, p3.uid]))
        self.assertEqual(set([p2.uid]),
                         set(p1[cuds.classes.HasChild].keys()))
        self.assertEqual(set([p2.uid]),
                         set(p3[cuds.classes.HasChild].keys()))
        self.assertEqual(set([p4.uid]), set(
            p2[cuds.classes.HasChild].keys()))

        # check passive relationships
        self.assertEqual(set([c.uid]),
                         set(p1[cuds.classes.IsInhabitantOf].keys()))
        self.assertEqual(set([p1.uid, p3.uid]),
                         set(p2[cuds.classes.IsChildOf].keys()))
        self.assertEqual(set([c.uid]),
                         set(p2[cuds.classes.IsInhabitantOf].keys()))
        self.assertEqual(set([c.uid]),
                         set(p3[cuds.classes.IsInhabitantOf].keys()))
        self.assertEqual(set([p2.uid]), set(p4[cuds.classes.IsChildOf].keys()))

        # check if items correctly added in second session
        # active relations
        self.assertEqual(set(cw[cuds.classes.HasInhabitant].keys()),
                         set([p1w.uid, p2w.uid]))
        self.assertEqual(set([p2w.uid]),
                         set(p1w[cuds.classes.HasChild].keys()))
        self.assertEqual(set([p4w.uid]),
                         set(p2w[cuds.classes.HasChild].keys()))

        # passive relations
        self.assertEqual(set([cw.uid]),
                         set(p1w[cuds.classes.IsInhabitantOf].keys()))
        self.assertEqual(set([p1w.uid]),
                         set(p2w[cuds.classes.IsChildOf].keys()))
        self.assertEqual(set([cw.uid]),
                         set(p2w[cuds.classes.IsInhabitantOf].keys()))
        self.assertEqual(set([p2w.uid]),
                         set(p4w[cuds.classes.IsChildOf].keys()))

    def test_fix_neighbours(self):
        w1 = cuds.classes.CityWrapper(session=CoreSession())
        w2 = cuds.classes.CityWrapper(session=CoreSession())

        c1w1 = cuds.classes.City("city1")  # parent in both wrappers
        c2w1 = cuds.classes.City("city2")  # parent in w1, not present in w2
        c3w1 = cuds.classes.City("city3")  # parent only in w1, present in w2
        c4w1 = cuds.classes.City("city4")  # parent only in w2
        p1w1 = cuds.classes.Citizen(name="citizen")
        p2w1 = cuds.classes.Citizen(name="child")

        w2.add(c1w1, c3w1, c4w1)
        c1w2, c3w2, c4w2 = w2.get(c1w1.uid, c3w1.uid, c4w1.uid)
        c1w2.add(p1w1, rel=cuds.classes.HasInhabitant)
        c4w2.add(p1w1, rel=cuds.classes.HasInhabitant)
        p1w2 = c1w2.get(p1w1.uid)
        p1w2.add(p2w1, rel=cuds.classes.HasChild)
        p2w2 = p1w2.get(p2w1.uid)

        w1.add(c1w1, c2w1, c3w1, c4w1)
        c1w1.add(p1w1, rel=cuds.classes.HasInhabitant)
        c2w1.add(p1w1, rel=cuds.classes.HasInhabitant)
        c3w1.add(p1w1, rel=cuds.classes.HasInhabitant)

        self.assertEqual(
            set(p1w1[cuds.classes.IsInhabitantOf].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid]))
        self.assertEqual(
            set(p2w2[cuds.classes.IsChildOf].keys()),
            set([p1w2.uid]))

        missing = dict()
        cuds.classes.Cuds._fix_neighbours(new_cuds_object=p1w1,
                                          old_cuds_object=p1w2,
                                          session=p1w2.session,
                                          missing=missing)

        # check if connections cuds_objects that are no
        # longer parents are in the missing dict
        self.assertIn(c2w1.uid, missing)
        self.assertEqual(
            set(p1w1[cuds.classes.IsInhabitantOf].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid, c4w1.uid]))
        self.assertNotIn(cuds.classes.IsPartOf, p2w2)

        # check if there are no unexpected other changes
        self.assertEqual(
            set(c1w1[cuds.classes.HasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c2w1[cuds.classes.HasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w1[cuds.classes.HasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertNotIn(cuds.classes.HasInhabitant, c4w1)

        # check if the parents in w2 have been updated
        self.assertEqual(
            set(c1w2[cuds.classes.HasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w2[cuds.classes.HasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c4w2[cuds.classes.HasInhabitant].keys()),
            set([p1w1.uid]))

    def test_get(self):
        """
        Tests the standard, normal behaviour of the get() method.

         - get()
         - get(*uids)
         - get(rel)
         - get(cuba_key)
         - get(*uids, rel)
         - get(rel, cuba_key)
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        p = cuds.classes.Citizen(name="John Smith")
        q = cuds.classes.Citizen(name="Jane Doe")
        c.add(n)
        c.add(p, q, rel=cuds.classes.HasInhabitant)

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
        get_has_part = c.get(rel=cuds.classes.HasInhabitant)
        self.assertEqual(set(get_has_part), {p, q})
        get_encloses = c.get(rel=cuds.classes.Encloses)
        self.assertEqual(set(get_encloses), {n, p, q})
        get_inhabits = c.get(rel=cuds.classes.IsInhabitantOf)
        self.assertEqual(get_inhabits, [])

        # get(cuba_key)
        get_citizen = c.get(cuba_key=cuds.classes.CUBA.CITIZEN)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(cuba_key=cuds.classes.CUBA.BUILDING)
        self.assertEqual(get_building, [])
        get_citizen = c.get(cuba_key=cuds.classes.CUBA.PERSON)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(
            cuba_key=cuds.classes.CUBA.ARCHITECTURAL_STRUCTURE)
        self.assertEqual(get_building, [])

        # get(*uids, rel)
        get_has_part_p = c.get(p.uid, rel=cuds.classes.HasInhabitant)
        self.assertEqual(get_has_part_p, p)

        get_has_part_q = c.get(q.uid, rel=cuds.classes.HasPart)
        self.assertEqual(get_has_part_q, None)

        # get(rel, cuba_key)
        get_inhabited_citizen = c.get(rel=cuds.classes.HasInhabitant,
                                      cuba_key=cuds.classes.CUBA.CITIZEN)
        self.assertEqual(set(get_inhabited_citizen), {p, q})

    def test_get_throws_exception(self):
        """
        Tests the get() method for unusual behaviours.

         - Getting with a wrong type
         - Getting with a not allowed combination of arguments
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        c.add(n)

        self.assertRaises(TypeError, c.get, "not a proper key")
        self.assertRaises(RuntimeError, c.get,
                          n.uid,
                          cuba_key=cuds.classes.CUBA.NEIGHBOURHOOD)

    def test_update(self):
        """
        Tests the standard, normal behaviour of the update() method.
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        new_n = create_from_cuds_object(n, CoreSession())
        new_s = cuds.classes.Street("a new street")
        new_n.add(new_s)
        c.add(n)

        old_neighbourhood = c.get(n.uid)
        old_streets = old_neighbourhood.get(
            cuba_key=cuds.classes.CUBA.STREET)
        self.assertEqual(old_streets, [])

        c.update(new_n)

        new_neighbourhood = c.get(n.uid)
        self.assertIs(new_neighbourhood, n)
        new_streets = new_neighbourhood.get(
            cuba_key=cuds.classes.CUBA.STREET)
        self.assertEqual(new_streets, [new_s])

    def test_remove(self):
        """
        Tests the standard, normal behaviour of the remove() method.

         - remove()
         - remove(*uids/DataContainers)
         - remove(rel)
         - remove(cuba_key)
         - remove(rel, cuba_key)
         - remove(*uids/DataContainers, rel)
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        p = cuds.classes.Citizen(name="John Smith")
        q = cuds.classes.Citizen(name="Jane Doe")
        c.add(n)
        c.add(q, p, rel=cuds.classes.HasInhabitant)

        self.assertIn(cuds.classes.HasPart, c)
        self.assertIn(cuds.classes.HasInhabitant, c)

        # remove()
        c.remove()
        self.assertFalse(c)
        # inverse
        get_inverse = p.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers)
        c.add(n)
        c.add(p, q, rel=cuds.classes.HasInhabitant)
        get_all = c.get()
        self.assertIn(p, get_all)
        c.remove(p.uid)
        get_all = c.get()
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [])

        # remove(rel)
        c.remove(rel=cuds.classes.HasPart)
        self.assertNotIn(cuds.classes.CUBA.HAS_PART, c)
        # inverse
        get_inverse = n.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [])

        # remove(cuba_key)
        c.remove(cuba_key=cuds.classes.CUBA.CITIZEN)
        self.assertNotIn(q, c.get())
        # inverse
        get_inverse = q.get(rel=cuds.classes.IsInhabitantOf)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers, rel)
        c.add(p, q, rel=cuds.classes.HasInhabitant)
        self.assertIn(cuds.classes.HasInhabitant, c)
        c.remove(q, p, rel=cuds.classes.HasInhabitant)
        self.assertNotIn(cuds.classes.HasInhabitant, c)
        # inverse
        get_inverse = p.get(rel=cuds.classes.IsInhabitantOf)
        self.assertEqual(get_inverse, [])

        # remove(rel, cuba_key)
        c.add(p, rel=cuds.classes.HasInhabitant)
        c.add(n)
        c.remove(rel=cuds.classes.HasInhabitant,
                 cuba_key=cuds.classes.CUBA.CITIZEN)
        get_all = c.get()
        self.assertIn(n, get_all)
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=cuds.classes.IsInhabitantOf)
        self.assertEqual(get_inverse, [])

    def test_remove_throws_exception(self):
        """
        Tests the remove() method for unusual behaviours.

         - Removing with a wrong key
         - Removing something non-existent
         - Removing with a not allowed argument combination
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")

        # Wrong key
        self.assertRaises(TypeError, c.remove, "not a proper key")

        # Non-existent
        self.assertRaises(RuntimeError, c.remove, n.uid)
        self.assertRaises(RuntimeError, c.remove, rel=cuds.classes.HasPart)
        self.assertRaises(RuntimeError, c.remove,
                          cuba_key=cuds.classes.CUBA.STREET)
        self.assertRaises(
            RuntimeError, c.remove, n.uid, rel=cuds.classes.HasPart)

        # Wrong arguments
        self.assertRaises(RuntimeError, c.remove, n.uid,
                          cuba_key=cuds.classes.CUBA.STREET)

    def test_update_throws_exception(self):
        """
        Tests the update() method for unusual behaviours.

         - Update an element that wasn't added before
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        c.add(n)
        p = cuds.classes.Citizen()
        self.assertRaises(ValueError, c.update, p)

    def test_iter(self):
        """
        Tests the iter() method when no cuba key is provided.
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        p = cuds.classes.Citizen(name="John Smith")
        q = cuds.classes.Citizen(name="Jane Doe")
        c.add(n)
        c.add(p, q, rel=cuds.classes.HasInhabitant)

        elements = set(list(c.iter()))
        self.assertEqual(elements, {n, p, q})

    def test_check_valid_add(self):
        """Check if _check_valid_add throws exceptions when illegal
        relationships are added.
        """
        c = cuds.classes.PopulatedPlace("Freiburg")
        p1 = cuds.classes.Person(name="Peter")
        c.add(p1, rel=cuds.classes.HasWorker)
        p2 = cuds.classes.Citizen(name="Martin")
        c.add(p2, rel=cuds.classes.HasWorker)
        p3 = cuds.classes.LivingBeing(name="Mimi")
        self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)
        c.remove()

        c.add(p1, rel=cuds.classes.HasMajor)
        c.add(p2, rel=cuds.classes.HasMajor)
        self.assertRaises(ValueError, c.add, p1, rel=cuds.classes.HasPart)

        c = cuds.classes.City("Freiburg")
        c.add(p1, rel=cuds.classes.HasWorker)
        c.add(p2, rel=cuds.classes.HasWorker)
        self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)

        c = cuds.classes.GeographicalPlace("Freiburg")
        self.assertRaises(ValueError, c.add, p1, rel=cuds.classes.HasWorker)
        self.assertRaises(ValueError, c.add, p2, rel=cuds.classes.HasWorker)
        self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)

        Cuds.CUDS_SETTINGS["check_relationship_supported"] = False
        c.add(p1, rel=cuds.classes.HasWorker)
        c.add(p2, rel=cuds.classes.HasWorker)
        c.add(p3, rel=cuds.classes.HasWorker)
        Cuds.CUDS_SETTINGS["check_relationship_supported"] = True

    def test_recursive_store(self):
        """Check if _recursive_store correctly stores cuds_objects recursively,
        correcting dangling and one-way connections.
        """
        c = cuds.classes.City("Freiburg")
        with CoreSession() as session:
            w = cuds.classes.CityWrapper(session=session)
            cw = w.add(c)

            p1 = cuds.classes.Citizen()
            p2 = cuds.classes.Citizen()
            p3 = cuds.classes.Citizen()
            p4 = cuds.classes.Citizen()
            c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
            p3.add(p1, p2, rel=cuds.classes.IsChildOf)
            p3.add(p4, rel=cuds.classes.HasChild)

            cw = w._recursive_store(c, cw)

            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            p4w = p3w.get(p4.uid)

            self.assertEqual(w.get(rel=cuds.classes.HasPart), [cw])
            self.assertEqual(
                set(cw.get(rel=cuds.classes.HasInhabitant)),
                {p1w, p2w, p3w}
            )
            self.assertEqual(
                set(cw.get(rel=cuds.classes.IsPartOf)),
                {w}
            )

            self.assertEqual(p3w.get(rel=cuds.classes.IsInhabitantOf), [cw])
            self.assertEqual(
                set(p3w.get(rel=cuds.classes.IsChildOf)),
                {p1w, p2w}
            )
            self.assertEqual(p3w.get(rel=cuds.classes.HasChild), [p4w])

    def test_fix_new_parents(self):
        """Check that _fix_new_parent:
        - Deletes connection to new parents not available in new session
        - Adds connection to new parents available in new session
        """
        n = cuds.classes.Neighbourhood("Zähringen")
        # parent in both sessions
        c1 = cuds.classes.City("Berlin")
        # only parent in default session (available in both)
        c2 = cuds.classes.City("Paris")
        n.add(c1, c2, rel=cuds.classes.IsPartOf)

        with CoreSession() as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            c1w, c2w = wrapper.add(c1, c2)
            nw = c2w.get(n.uid)
            nw.remove(c2.uid, rel=cuds.classes.Relationship)

            # only parent + available in default session
            c3 = cuds.classes.City("London")
            n.add(c3, rel=cuds.classes.IsPartOf)

            n = clone_cuds_object(n)
            n._session = session
            new_parent_diff = get_neighbour_diff(
                n, nw, rel=cuds.classes.PassiveRelationship)
            new_parents = session.load(*[x[0] for x in new_parent_diff])

            missing = dict()
            Cuds._fix_new_parents(new_cuds_object=n,
                                  new_parents=new_parents,
                                  new_parent_diff=new_parent_diff,
                                  missing=missing)

        self.assertEqual(
            set(n.get(rel=cuds.classes.IsPartOf)),
            {c1w, c2w, None}  # missing parent, should be in missing dict
        )
        self.assertEqual(missing, {c3.uid: [(n, cuds.classes.IsPartOf)]})
        self.assertEqual(c2w.get(rel=cuds.classes.HasPart), [n])

    def test_fix_old_neighbours(self):
        """Check if _fix_old_neighbours.
        - Deletes old children.
        - Adds connection to old parents.
        """
        c = cuds.classes.City("Freiburg")

        with CoreSession() as session:
            wrapper = cuds.classes.CityWrapper(session=session)
            cw = wrapper.add(c)
            n = cuds.classes.Neighbourhood("Zähringen")
            nw = cw.add(n)

            c = clone_cuds_object(c)
            c._session = session
            old_neighbour_diff = get_neighbour_diff(cw, c)
            old_neighbours = session.load(*[x[0] for x in old_neighbour_diff])
            Cuds._fix_old_neighbours(new_cuds_object=c,
                                     old_cuds_object=cw,
                                     old_neighbours=old_neighbours,
                                     old_neighbour_diff=old_neighbour_diff)
        self.assertEqual(c.get(rel=cuds.classes.IsPartOf), [wrapper])
        self.assertEqual(c.get(rel=cuds.classes.HasPart), [])
        self.assertEqual(nw.get(rel=cuds.classes.IsPartOf), [])
        self.assertEqual(wrapper.get(rel=cuds.classes.HasPart), [c])

    def test_add_twice(self):
        """ Test what happens if you add the same
        object twice to a new session"""
        p = cuds.classes.Citizen(name="Ralf")
        c1 = cuds.classes.City("Freiburg")
        c2 = cuds.classes.City("Offenburg")
        with CoreSession() as session:
            w = cuds.classes.CityWrapper(session=session)
            c1w, c2w = w.add(c1, c2)
            pw1 = c1w.add(p, rel=cuds.classes.HasInhabitant)
            pw2 = c2w.add(p, rel=cuds.classes.HasInhabitant)
            self.assertIs(pw1, pw2)
            self.assertEqual(set(pw1.get(rel=cuds.classes.IsInhabitantOf)),
                             {c1w, c2w})


if __name__ == '__main__':
    unittest.main()
