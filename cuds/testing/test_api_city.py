# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import uuid
from copy import deepcopy

from cuds.classes.core.session.core_session import CoreSession
import cuds.classes


class TestAPICity(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        self.assertRaises(TypeError,
                          cuds.classes.City, "name", "uid", "unwanted")

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

        c.add(p, rel=cuds.classes.IsInhabitedBy)
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
        """Tests if add() works correctly if added cuds is from another session.
        """
        c = cuds.classes.City("City")
        p1 = cuds.classes.Citizen()
        c.add(p1, rel=cuds.classes.IsInhabitedBy)

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
        c.add(p2, p3, rel=cuds.classes.IsInhabitedBy)
        p1.add(p2, rel=cuds.classes.IsParentOf)
        p3.add(p2, rel=cuds.classes.IsParentOf)
        p2.add(p4, rel=cuds.classes.IsParentOf)

        cw.add(p2, rel=cuds.classes.IsInhabitedBy)
        p2w = cw.get(p2.uid)
        p4w = p2w.get(p4.uid)

        # check if there are unexpected changes in the first session
        # first check active relationships
        self.assertEqual(set(c[cuds.classes.IsInhabitedBy].keys()),
                         set([p1.uid, p2.uid, p3.uid]))
        self.assertEqual(set([p2.uid]),
                         set(p1[cuds.classes.IsParentOf].keys()))
        self.assertEqual(set([p2.uid]),
                         set(p3[cuds.classes.IsParentOf].keys()))
        self.assertEqual(set([p4.uid]), set(
            p2[cuds.classes.IsParentOf].keys()))

        # check passive relationships
        self.assertEqual(set([c.uid]), set(p1[cuds.classes.Inhabits].keys()))
        self.assertEqual(set([p1.uid, p3.uid]),
                         set(p2[cuds.classes.IsChildOf].keys()))
        self.assertEqual(set([c.uid]),
                         set(p2[cuds.classes.Inhabits].keys()))
        self.assertEqual(set([c.uid]), set(p3[cuds.classes.Inhabits].keys()))
        self.assertEqual(set([p2.uid]), set(p4[cuds.classes.IsChildOf].keys()))

        # check if items correctly added in second session
        # active relations
        self.assertEqual(set(cw[cuds.classes.IsInhabitedBy].keys()),
                         set([p1w.uid, p2w.uid]))
        self.assertEqual(set([p2w.uid]),
                         set(p1w[cuds.classes.IsParentOf].keys()))
        self.assertEqual(set([p4w.uid]),
                         set(p2w[cuds.classes.IsParentOf].keys()))

        # passive relations
        self.assertEqual(set([cw.uid]),
                         set(p1w[cuds.classes.Inhabits].keys()))
        self.assertEqual(set([p1w.uid]),
                         set(p2w[cuds.classes.IsChildOf].keys()))
        self.assertEqual(set([cw.uid]),
                         set(p2w[cuds.classes.Inhabits].keys()))
        self.assertEqual(set([p2w.uid]),
                         set(p4w[cuds.classes.IsChildOf].keys()))

    def test_fix_neighbors(self):
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
        c1w2.add(p1w1, rel=cuds.classes.IsInhabitedBy)
        c4w2.add(p1w1, rel=cuds.classes.IsInhabitedBy)
        p1w2 = c1w2.get(p1w1.uid)
        p1w2.add(p2w1, rel=cuds.classes.IsParentOf)
        p2w2 = p1w2.get(p2w1.uid)

        w1.add(c1w1, c2w1, c3w1, c4w1)
        c1w1.add(p1w1, rel=cuds.classes.IsInhabitedBy)
        c2w1.add(p1w1, rel=cuds.classes.IsInhabitedBy)
        c3w1.add(p1w1, rel=cuds.classes.IsInhabitedBy)

        self.assertEqual(
            set(p1w1[cuds.classes.Inhabits].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid]))
        self.assertEqual(
            set(p2w2[cuds.classes.IsChildOf].keys()),
            set([p1w2.uid]))

        missing = dict()
        cuds.classes.Cuds._fix_neighbors(new_cuds=p1w1,
                                         old_cuds=p1w2,
                                         session=p1w2.session,
                                         missing=missing)

        # check if connections cuds objects that are no
        # longer parents are in the missing dict
        self.assertIn(c2w1.uid, missing)
        self.assertEqual(
            set(p1w1[cuds.classes.Inhabits].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid, c4w1.uid]))
        self.assertNotIn(cuds.classes.IsPartOf, p2w2)

        # check if there are no unexpected other changes
        self.assertEqual(
            set(c1w1[cuds.classes.IsInhabitedBy].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c2w1[cuds.classes.IsInhabitedBy].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w1[cuds.classes.IsInhabitedBy].keys()),
            set([p1w1.uid]))
        self.assertNotIn(cuds.classes.IsInhabitedBy, c4w1)

        # check if the parents in w2 have been updated
        self.assertEqual(
            set(c1w2[cuds.classes.IsInhabitedBy].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w2[cuds.classes.IsInhabitedBy].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c4w2[cuds.classes.IsInhabitedBy].keys()),
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
        c.add(p, q, rel=cuds.classes.IsInhabitedBy)

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
        get_has_part = c.get(rel=cuds.classes.IsInhabitedBy)
        self.assertEqual(set(get_has_part), {p, q})
        get_encloses = c.get(rel=cuds.classes.Encloses)
        self.assertEqual(set(get_encloses), {n, p, q})
        get_inhabits = c.get(rel=cuds.classes.Inhabits)
        self.assertEqual(get_inhabits, [])

        # get(cuba_key)
        get_citizen = c.get(cuba_key=cuds.classes.CUBA.CITIZEN)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(cuba_key=cuds.classes.CUBA.BUILDING)
        self.assertEqual(get_building, [])

        # get(*uids, rel)
        get_has_part_p = c.get(p.uid, rel=cuds.classes.IsInhabitedBy)
        self.assertEqual(get_has_part_p, p)

        get_has_part_q = c.get(q.uid, rel=cuds.classes.HasPart)
        self.assertEqual(get_has_part_q, None)

        # get(rel, cuba_key)
        get_inhabited_citizen = c.get(rel=cuds.classes.IsInhabitedBy,
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
        new_n = deepcopy(n)
        new_s = cuds.classes.Street("a new street")
        new_n.add(new_s)
        c.add(n)

        old_neighbourhood = c.get(n.uid)
        old_streets = old_neighbourhood.get(
            cuba_key=cuds.classes.CUBA.STREET)
        self.assertEqual(old_streets, [])

        c.update(new_n)

        new_neighbourhood = c.get(n.uid)
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
        c.add(q, p, rel=cuds.classes.IsInhabitedBy)

        self.assertIn(cuds.classes.HasPart, c)
        self.assertIn(cuds.classes.IsInhabitedBy, c)

        # remove()
        c.remove()
        self.assertFalse(c)
        # inverse
        get_inverse = p.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers)
        c.add(n)
        c.add(p, q, rel=cuds.classes.IsInhabitedBy)
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
        get_inverse = q.get(rel=cuds.classes.Inhabits)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers, rel)
        c.add(p, q, rel=cuds.classes.IsInhabitedBy)
        self.assertIn(cuds.classes.IsInhabitedBy, c)
        c.remove(q, p, rel=cuds.classes.IsInhabitedBy)
        self.assertNotIn(cuds.classes.IsInhabitedBy, c)
        # inverse
        get_inverse = p.get(rel=cuds.classes.Inhabits)
        self.assertEqual(get_inverse, [])

        # remove(rel, cuba_key)
        c.add(p, rel=cuds.classes.IsInhabitedBy)
        c.add(n)
        c.remove(rel=cuds.classes.IsInhabitedBy,
                 cuba_key=cuds.classes.CUBA.CITIZEN)
        get_all = c.get()
        self.assertIn(n, get_all)
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=cuds.classes.Inhabits)
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
        c.add(p, q, rel=cuds.classes.IsInhabitedBy)

        elements = set(list(c.iter()))
        self.assertEqual(elements, {n, p, q})


if __name__ == '__main__':
    unittest.main()
