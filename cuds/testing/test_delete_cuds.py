# # Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# # at Fraunhofer IWM.
# # All rights reserved.
# # Redistribution and use are limited to the scope agreed with the end user.
# # No parts of this software may be used outside of this context.
# # No redistribution is allowed without explicit written permission.
#
# import unittest2 as unittest
# from uuid import UUID
#
# import cuds.classes
# from cuds.utils import find_cuds
# from cuds.utils import delete_cuds
# from cuds.utils import pretty_print
#
#
# class TestDeleteCUDS(unittest.TestCase):
#     def setUp(self):
#         self.c = cuds.classes.Cuds(name="CUDS")
#         self.water_molecule_cuds = cuds.classes.Molecule("Water Molecule")
#
#         self.oxygen = cuds.classes.Atom("Oxygen")
#         self.oxygen_mass = cuds.classes.Mass("u", 15.999)
#         self.oxygen.add(self.oxygen_mass)
#
#         self.hydrogen1 = cuds.classes.Atom("Hydrogen 1")
#         self.hydrogen2 = cuds.classes.Atom("Hydrogen 2")
#         self.hydrogen_mass = cuds.classes.Mass("u", 1.00784)
#         self.hydrogen1.add(self.hydrogen_mass)
#         self.hydrogen2.add(self.hydrogen_mass)
#
#         self.water_molecule_cuds.add(self.oxygen,
#                                      self.hydrogen1,
#                                      self.hydrogen2)
#         self.c.add(self.water_molecule_cuds)
#
#     def test_delete_first_level_child(self):
#         self.assertTrue(delete_cuds(self.water_molecule_cuds.uid, self.c),
#                         "delete_cuds() have to return True.")
#         self.assertTrue(find_cuds(self.water_molecule_cuds.uid, self.c)
#                         is None,
#                         "The element was not deleted successfully.")
#
#     def test_delete_second_level_child(self):
#         self.assertTrue(delete_cuds(self.oxygen.uid, self.c),
#                         "delete_cuds() have to return True.")
#         self.assertTrue(find_cuds(self.oxygen.uid, self.c) is None,
#                         "The element was not deleted successfully.")
#
#     def test_delete_third_level_child(self):
#         self.assertTrue(delete_cuds(self.oxygen_mass.uid, self.c),
#                         "delete_cuds() have to return True.")
#         self.assertTrue(find_cuds(self.oxygen_mass.uid, self.c) is None,
#                         "The element was not deleted successfully.")
#
#     def test_delete_root_element(self):
#         self.assertFalse(delete_cuds(self.c.uid, self.c),
#                          "delete_cuds() have to return False.")
#         self.assertFalse(find_cuds(self.c.uid, self.c) is None,
#                          "The root element was deleted.")
#
#     def test_delete_non_existing_element(self):
#         non_existent_uuid = False
#         while not non_existent_uuid:
#             dummy_uuid = UUID
#             if find_cuds(dummy_uuid, self.c) is None:
#                 non_existent_uuid = True
#                 self.assertFalse(delete_cuds(dummy_uuid, self.c),
#                                  "delete_cuds() have to return False.")
#
#     def test_delete_multiple_occurrences(self):
#         self.assertTrue(delete_cuds(self.hydrogen_mass.uid, self.c),
#                         "delete_cuds() have to return True.")
#         self.assertTrue(find_cuds(self.hydrogen_mass.uid, self.c) is None,
#                         "The element was not deleted successfully.")
#
#
# if __name__ == '__main__':
#     suite = unittest.TestLoader().loadTestsFromTestCase(TestDeleteCUDS)
#     unittest.TextTestRunner(verbosity=2).run(suite)
