import unittest
from uuid import UUID

import cuds.classes as cuds


class TestAPI(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        self.assertRaises(TypeError, cuds.Cuds, "name", "something else")

        c = cuds.Cuds(name="CUDS")
        d = cuds.ComputationalBoundary()
        self.assertIsInstance(c, cuds.Cuds)
        self.assertIsInstance(d, cuds.ComputationalBoundary)

    def test_name(self):
        """
        Tests that the name is assigned properly
        """
        c = cuds.Cuds("Cuds")
        self.assertEqual(str(c.name), "Cuds")

    def test_uid(self):
        """
        Tests that the uid variable contains a UUID object
        """
        c = cuds.Cuds("Cuds")
        self.assertIsInstance(c.uid, UUID)

    def test_set_throws_exception(self):
        """
        Tests that setting a value for a key not in restricted
        keys throws an exception.
        """
        c = cuds.Cuds("Cuds")
        self.assertRaises(ValueError, c.__setitem__, "not an allowed key", 15)

    def test_add(self):
        """
        Tests the standard, normal behaviour of the add() method
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary(name="ComputationalBoundary")
        d.uid = UUID('61d5422a-884a-4986-aef5-25419482d959')
        c.add(d)
        self.assertEqual(str(c), "{<CUBA.COMPUTATIONAL_BOUNDARY: "
                                 "'COMPUTATIONAL_BOUNDARY'>: "
                                 "{UUID('61d5422a-884a-4986-aef5-25419482d959'"
                                 "): "
                                 "{}}}")
        e = cuds.ComputationalBoundary()
        e.uid = UUID('07d5422a-884a-4986-aef5-25419482d959')
        c.add(e)
        self.assertEqual(str(c), "{<CUBA.COMPUTATIONAL_BOUNDARY: "
                                 "'COMPUTATIONAL_BOUNDARY'>: {"
                                 "UUID('61d5422a-884a-4986-aef5-25419482d959')"
                                 ": {}, "
                                 "UUID('07d5422a-884a-4986-aef5-25419482d959'"
                                 "): "
                                 "{}}}")

    def test_add_throws_exception(self):
        """
        Tests the add() method for unusual behaviours.

         - Adding an unsupported object
         - Adding an object that is already there
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary(name="ComputationalBoundary")
        self.assertRaises(TypeError, c.add, "Not a CUDS objects")
        c.add(d)
        self.assertRaises(ValueError, c.add, d)

    def test_get(self):
        """
        Tests the standard, normal behaviour of the get() method.

         - By uid
         - By cuba key
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary(name="ComputationalBoundary")
        c.add(d)
        e = cuds.ComputationalBoundary()
        c.add(e)
        m = cuds.Material()
        c.add(m)
        # Get returns a list, remember to access first element:
        d_by_get = c.get(d.uid)[0]
        self.assertEqual(d_by_get, d)
        self.assertIn(d, c.get(cuds.CUBA.COMPUTATIONAL_BOUNDARY))
        self.assertIn(e, c.get(cuds.CUBA.COMPUTATIONAL_BOUNDARY))

    def test_get_throws_exception(self):
        """
        Tests the get() method for unusual behaviours.

         - Getting with something that is not a uid
        """
        c = cuds.Cuds("Cuds")
        self.assertRaises(TypeError, c.get, "not a proper key")

    def test_update(self):
        """
        Tests the standard, normal behaviour of the update() method.
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary(name="ComputationalBoundary")
        c.add(d)
        d.name = "New name"
        c.update(d)
        self.assertEqual(c.get(d.uid)[0].name, d.name)

    def test_update_throws_exception(self):
        """
        Tests the update() method for unusual behaviours.

         - Update an element that wasn't added before
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary(name="ComputationalBoundary")
        c.add(d)
        m = cuds.Material("Material not in c")
        self.assertRaises(ValueError, c.update, m)

    def test_remove(self):
        """
        Tests the standard, normal behaviour of the remove() method.

         - Should erase the reference from the given object, not from others
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary("ComputationalBoundary")
        m = cuds.Material()
        d.add(m)
        c.add(d)
        c.add(m)  # m is now in d and c
        d.remove(m)
        self.assertNotIn(m, d.get(cuds.CUBA.MATERIAL))
        self.assertIn(m, c.get(cuds.CUBA.MATERIAL))

    def test_remove_throws_exception(self):
        """
        Tests the remove() method for unusual behaviours.

         - Removing with a wrong key
         - Removing something non-existent
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary("ComputationalBoundary")
        self.assertRaises(TypeError, c.remove, "not a proper key")
        self.assertRaises(KeyError, c.remove, d.uid)

    def test_iter_all(self):
        """
        Tests the iter() method when no cuba key is provided.
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary("ComputationalBoundary")
        m = cuds.Material()
        c.add(d)
        c.add(m)
        for obj in c.iter():
            self.assertIsInstance(obj, cuds.DataContainer)

    def test_iter_by_key(self):
        """
        Tests the iter() method when a cuba key is provided.
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary("ComputationalBoundary")
        m = cuds.Material()
        c.add(d)
        c.add(m)
        for obj in c.iter(cuds.CUBA.COMPUTATIONAL_BOUNDARY):
            self.assertIsInstance(obj, cuds.ComputationalBoundary)

    def test_iter_throws_exception(self):
        """
        Tests the iter() method for unusual behaviours.
        """
        c = cuds.Cuds("Cuds")
        d = cuds.ComputationalBoundary("ComputationalBoundary")
        c.add(d)
        self.assertRaises(TypeError, next, c.iter("This is not a proper key"))


if __name__ == '__main__':
    unittest.main()
