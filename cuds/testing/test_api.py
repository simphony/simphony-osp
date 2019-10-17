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
                          cuds.classes.Entity, "name", "something else")

        e = cuds.classes.Entity()
        m = cuds.classes.MaterialRelation()
        self.assertIsInstance(e, cuds.classes.Entity)
        self.assertIsInstance(m, cuds.classes.MaterialRelation)

    def test_properties(self):
        """
        Tests that properties are assigned properly
        """
        a = cuds.classes.ActivationEnergy(5)
        self.assertEqual(a.value, 5)

    def test_uid(self):
        """
        Tests that the uid variable contains a UUID object
        """
        e = cuds.classes.Entity()
        self.assertIsInstance(e.uid, UUID)

    def test_set_throws_exception(self):
        """
        Tests that setting a value for a key not in restricted
        keys throws an exception.
        """
        e = cuds.classes.Entity()
        self.assertRaises(ValueError, e.__setitem__, "not an allowed key", 15)

    def test_add(self):
        """
        Tests the standard, normal behaviour of the add() method
        """
        e = cuds.classes.Entity()
        m = cuds.classes.MaterialRelation()
        m.uid = UUID('61d5422a-884a-4986-aef5-25419482d959')
        e.add(m)
        self.assertEqual(str(e.get(m.uid)[0].uid),
                         '61d5422a-884a-4986-aef5-25419482d959')

    def test_add_throws_exception(self):
        """
        Tests the add() method for unusual behaviours.

         - Adding an unsupported object
         - Adding an object that is already there
        """
        e = cuds.classes.Entity()
        m = cuds.classes.MaterialRelation()
        self.assertRaises(TypeError, e.add, "Not a CUDS objects")
        e.add(m)
        self.assertRaises(ValueError, e.add, m)

    def test_get(self):
        """
        Tests the standard, normal behaviour of the get() method.

         - By uid
         - By cuba key
        """
        e = cuds.classes.Entity()
        m1 = cuds.classes.MaterialRelation()
        e.add(m1)
        m2 = cuds.classes.MaterialRelation()
        e.add(m2)
        # Get returns a list, remember to access first element:
        m1_by_get = e.get(m1.uid)[0]
        self.assertEqual(m1_by_get, m1)
        self.assertIn(m1, e.get(cuds.classes.CUBA.MATERIAL_RELATION))
        self.assertIn(m2, e.get(cuds.classes.CUBA.MATERIAL_RELATION))

    def test_get_throws_exception(self):
        """
        Tests the get() method for unusual behaviours.

         - Getting with something that is not a uid
        """
        e = cuds.classes.Entity()
        self.assertRaises(TypeError, e.get, "not a proper key")

    def test_update(self):
        """
        Tests the standard, normal behaviour of the update() method.
        """
        e = cuds.classes.Entity()
        a = cuds.classes.ActivationEnergy(5)
        e.add(a)
        a.value = 7
        e.update(a)
        self.assertEqual(e.get(a.uid)[0].value, a.value)

    def test_update_throws_exception(self):
        """
        Tests the update() method for unusual behaviours.

         - Update an element that wasn't added before
        """
        e = cuds.classes.Entity()
        m1 = cuds.classes.MaterialRelation()
        e.add(m1)
        m2 = cuds.classes.MaterialRelation()
        self.assertRaises(ValueError, e.update, m2)

    def test_remove(self):
        """
        Tests the standard, normal behaviour of the remove() method.

         - Should erase the reference from the given object, not from others
        """
        e = cuds.classes.Entity()
        m1 = cuds.classes.MaterialRelation()
        m2 = cuds.classes.MaterialRelation()
        m2.add(m1)
        e.add(m2)
        e.add(m1)  # m1 is now in m2 and e
        m2.remove(m1)
        self.assertNotIn(m1, m2.get(cuds.classes.CUBA.MATERIAL_RELATION))
        self.assertIn(m1, e.get(cuds.classes.CUBA.MATERIAL_RELATION))

    def test_remove_throws_exception(self):
        """
        Tests the remove() method for unusual behaviours.

         - Removing with a wrong key
         - Removing something non-existent
        """
        e = cuds.classes.Entity()
        m = cuds.classes.MaterialRelation()
        self.assertRaises(TypeError, e.remove, "not a proper key")
        self.assertRaises(KeyError, e.remove, m.uid)

    def test_iter_all(self):
        """
        Tests the iter() method when no cuba key is provided.
        """
        e = cuds.classes.Entity()
        a = cuds.classes.ActivationEnergy(5)
        m = cuds.classes.MaterialRelation()
        e.add(a)
        e.add(m)
        for obj in e.iter():
            self.assertIsInstance(obj, cuds.classes.DataContainer)

    def test_iter_by_key(self):
        """
        Tests the iter() method when a cuba key is provided.
        """
        e = cuds.classes.Entity()
        a = cuds.classes.ActivationEnergy(5)
        m = cuds.classes.MaterialRelation()
        e.add(a)
        e.add(m)
        for obj in e.iter(cuds.classes.CUBA.MATERIAL_RELATION):
            self.assertIsInstance(obj, cuds.classes.MaterialRelation)

    def test_iter_throws_exception(self):
        """
        Tests the iter() method for unusual behaviours.
        """
        e = cuds.classes.Entity()
        e1 = cuds.classes.Entity()
        e.add(e1)
        self.assertRaises(TypeError, next, e.iter("This is not a proper key"))


if __name__ == '__main__':
    unittest.main()
