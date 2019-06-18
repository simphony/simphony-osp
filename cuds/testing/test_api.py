# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
from uuid import UUID

import cuds.classes


class TestAPI(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        self.assertRaises(TypeError,
                          cuds.classes.City, "unwanted parameter")

        c = cuds.classes.City()
        p = cuds.classes.Person()
        self.assertIsInstance(c, cuds.classes.City)
        self.assertIsInstance(p, cuds.classes.Person)

    def test_uid(self):
        """
        Tests that the uid variable contains a UUID object
        """
        c = cuds.classes.City()
        self.assertIsInstance(c.uid, UUID)

    def test_set_throws_exception(self):
        """
        Tests that setting a value for a key not in restricted
        keys throws an exception.
        """
        c = cuds.classes.City()
        self.assertRaises(ValueError, c.__setitem__, "not an allowed key", 15)

    def test_add(self):
        """
        Tests the standard, normal behaviour of the add() method
        """
        c = cuds.classes.City()
        n = cuds.classes.Neighbourhood()
        n.uid = UUID('61d5422a-884a-4986-aef5-25419482d959')
        c.add(n)
        self.assertEqual(str(c.get(n.uid)[0].uid),
                         '61d5422a-884a-4986-aef5-25419482d959')
        p = cuds.classes.Citizen()
        p.uid = UUID('07d5422a-884a-4986-aef5-25419482d959')
        c.add(n, cuds.classes.CUBA.ENCLOSES)
        self.assertEqual(str(c.get(p.uid)[0].uid),
                         '07d5422a-884a-4986-aef5-25419482d959')

    def test_add_throws_exception(self):
        """
        Tests the add() method for unusual behaviours.

         - Adding an unsupported object
         - Adding an object that is already there
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        self.assertRaises(TypeError, c.add, "Not a CUDS objects")
        c.add(d)
        self.assertRaises(ValueError, c.add, d)

    def test_get(self):
        """
        Tests the standard, normal behaviour of the get() method.

         - By uid
         - By cuba key
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        c.add(d)
        e = cuds.classes.ComputationalBoundary()
        c.add(e)
        m = cuds.classes.Material()
        c.add(m)
        # Get returns a list, remember to access first element:
        d_by_get = c.get(d.uid)[0]
        self.assertEqual(d_by_get, d)
        self.assertIn(d, c.get(cuds.classes.CUBA.COMPUTATIONAL_BOUNDARY))
        self.assertIn(e, c.get(cuds.classes.CUBA.COMPUTATIONAL_BOUNDARY))

    def test_get_throws_exception(self):
        """
        Tests the get() method for unusual behaviours.

         - Getting with something that is not a uid
        """
        c = cuds.classes.City()
        self.assertRaises(TypeError, c.get, "not a proper key")

    def test_update(self):
        """
        Tests the standard, normal behaviour of the update() method.
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        c.add(d)
        d.name = "New name"
        c.update(d)
        self.assertEqual(c.get(d.uid)[0].name, d.name)

    def test_update_throws_exception(self):
        """
        Tests the update() method for unusual behaviours.

         - Update an element that wasn't added before
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        c.add(d)
        m = cuds.classes.Material()
        self.assertRaises(ValueError, c.update, m)

    def test_remove(self):
        """
        Tests the standard, normal behaviour of the remove() method.

         - Should erase the reference from the given object, not from others
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        m = cuds.classes.Material()
        d.add(m)
        c.add(d)
        c.add(m)  # m is now in d and c
        d.remove(m)
        self.assertNotIn(m, d.get(cuds.classes.CUBA.MATERIAL))
        self.assertIn(m, c.get(cuds.classes.CUBA.MATERIAL))

    def test_remove_throws_exception(self):
        """
        Tests the remove() method for unusual behaviours.

         - Removing with a wrong key
         - Removing something non-existent
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        self.assertRaises(TypeError, c.remove, "not a proper key")
        self.assertRaises(KeyError, c.remove, d.uid)

    def test_iter_all(self):
        """
        Tests the iter() method when no cuba key is provided.
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        m = cuds.classes.Material()
        c.add(d)
        c.add(m)
        for obj in c.iter():
            self.assertIsInstance(obj, cuds.classes.DataContainer)

    def test_iter_by_key(self):
        """
        Tests the iter() method when a cuba key is provided.
        """
        c = cuds.classes.City()
        d = cuds.classes.ComputationalBoundary()
        m = cuds.classes.Material()
        c.add(d)
        c.add(m)
        for obj in c.iter():
            self.assertIsInstance(obj, cuds.classes.ComputationalBoundary)


if __name__ == '__main__':
    unittest.main()
