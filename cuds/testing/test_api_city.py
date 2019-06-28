# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import uuid
from copy import deepcopy

import cuds.classes


class TestAPICity(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        self.assertRaises(TypeError,
                          cuds.classes.City, "name", "unwanted parameter")

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

        n.uid = uuid.UUID('61d5422a-884a-4986-aef5-25419482d959')
        c.add(n)
        self.assertEqual(str(c.get(n.uid)[0].uid),
                         '61d5422a-884a-4986-aef5-25419482d959')

        # Test the inverse relationship
        get_inverse = n.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [c])

        p.uid = uuid.UUID('07d5422a-884a-4986-aef5-25419482d959')
        c.add(p, rel=cuds.classes.Encloses)
        self.assertEqual(str(c.get(p.uid)[0].uid),
                         '07d5422a-884a-4986-aef5-25419482d959')

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

    def test_get(self):
        """
        Tests the standard, normal behaviour of the get() method.

         - get()
         - get(*uids)
         - get(rel)
         - get(cuba_key)
         - get(*uids, rel)
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        p = cuds.classes.Citizen("John Smith")
        q = cuds.classes.Citizen("Jane Doe")
        c.add(n, p)
        c.add(q, rel=cuds.classes.Encloses)

        # get()
        get_default = c.get()
        self.assertEqual(set(get_default), {n, p})

        # get(*uids)
        get_p_uid = c.get(p.uid)
        self.assertEqual(get_p_uid, [p])
        get_q_uid = c.get(q.uid)
        self.assertEqual(get_q_uid, [q])
        get_nq_uid = c.get(n.uid, q.uid)
        self.assertEqual(set(get_nq_uid), {n, q})
        get_new_uid = c.get(uuid.uuid4())
        self.assertEqual(get_new_uid, [None])

        # get(rel)
        get_has_part = c.get(rel=cuds.classes.HasPart)
        self.assertEqual(set(get_has_part), {n, p})
        get_encloses = c.get(rel=cuds.classes.Encloses)
        self.assertEqual(get_encloses, [q])
        get_inhabits = c.get(rel=cuds.classes.Inhabits)
        self.assertEqual(get_inhabits, [None])

        # get(cuba_key)
        get_citizen = c.get(cuba_key=cuds.classes.CUBA.CITIZEN)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(cuba_key=cuds.classes.CUBA.BUILDING)
        self.assertEqual(get_building, [None])

        # get(*uids, rel)
        get_has_part_p = c.get(p.uid, rel=cuds.classes.HasPart)
        self.assertEqual(get_has_part_p, [p])

        get_has_part_q = c.get(q.uid, rel=cuds.classes.HasPart)
        self.assertEqual(get_has_part_q, [None])

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
        self.assertRaises(TypeError, c.get,
                          rel=cuds.classes.Inhabits,
                          cuba_key=cuds.classes.CUBA.CITIZEN)
        self.assertRaises(TypeError, c.get,
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

        old_neighbourhood = c.get(n.uid)[0]
        old_streets = old_neighbourhood.get(cuba_key=cuds.classes.CUBA.STREET)
        self.assertEqual(old_streets, [None])

        c.update(new_n)

        new_neighbourhood = c.get(n.uid)[0]
        new_streets = new_neighbourhood.get(cuba_key=cuds.classes.CUBA.STREET)
        self.assertEqual(new_streets, [new_s])

    def test_remove(self):
        """
        Tests the standard, normal behaviour of the remove() method.

         - remove(*uids/DataContainers)
         - remove(rel)
         - remove(cuba_key)
         - remove(*uids/DataContainers, rel)
        """
        c = cuds.classes.City("a city")
        n = cuds.classes.Neighbourhood("a neigbourhood")
        p = cuds.classes.Citizen("John Smith")
        q = cuds.classes.Citizen("Jane Doe")
        c.add(n, p)
        c.add(q, rel=cuds.classes.Encloses)

        self.assertIn(cuds.classes.CUBA.HAS_PART, c)
        self.assertIn(cuds.classes.CUBA.ENCLOSES, c)

        # remove(*uids/DataContainers)
        get_default = c.get()
        self.assertIn(p, get_default)
        c.remove(p.uid)
        get_default = c.get()
        self.assertNotIn(p, get_default)
        # inverse
        get_inverse = p.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [None])

        # remove(rel)
        c.remove(rel=cuds.classes.Encloses)
        self.assertNotIn(cuds.classes.CUBA.ENCLOSES, c)
        # inverse
        get_inverse = q.get(rel=cuds.classes.IsEnclosedBy)
        self.assertEqual(get_inverse, [None])

        # remove(cuba_key)
        c.remove(cuba_key=cuds.classes.CUBA.NEIGHBOURHOOD)
        self.assertNotIn(cuds.classes.CUBA.HAS_PART, c)
        # inverse
        get_inverse = n.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [None])

        # remove(*uids/DataContainers, rel)
        c.add(n, p)
        self.assertIn(cuds.classes.CUBA.HAS_PART, c)
        c.remove(n, p, rel=cuds.classes.HasPart)
        self.assertNotIn(cuds.classes.CUBA.HAS_PART, c)
        # inverse
        get_inverse = n.get(rel=cuds.classes.IsPartOf)
        self.assertEqual(get_inverse, [None])

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
        self.assertRaises(KeyError, c.remove, n.uid)
        self.assertRaises(KeyError, c.remove, rel=cuds.classes.HasPart)
        self.assertRaises(KeyError, c.remove,
                          cuba_key=cuds.classes.CUBA.STREET)
        self.assertRaises(KeyError, c.remove, n.uid, rel=cuds.classes.HasPart)

        # Wrong arguments
        self.assertRaises(TypeError, c.remove, n.uid,
                          cuba_key=cuds.classes.CUBA.STREET)
        self.assertRaises(TypeError, c.remove, rel=cuds.classes.HasPart,
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
        p = cuds.classes.Citizen("John Smith")
        q = cuds.classes.Citizen("Jane Doe")
        c.add(n, p)
        c.add(q, rel=cuds.classes.Encloses)

        elements = set(list(c.iter()))
        self.assertEqual(elements, {n, p, q})


if __name__ == '__main__':
    unittest.main()
