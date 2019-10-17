# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
from uuid import UUID

import cuds.classes
from cuds.utils import find_cuds


# Note: Comparison works by testing UUIDs
class TestDeleteCUDS(unittest.TestCase):
    def setUp(self):
        self.e = cuds.classes.Entity()
        self.water_molecule_cuds = cuds.classes.Molecule()

        self.oxygen = cuds.classes.Atom()
        self.oxygen_mass = cuds.classes.Mass()
        self.oxygen.add(self.oxygen_mass)

        self.hydrogen1 = cuds.classes.Atom()
        self.hydrogen2 = cuds.classes.Atom()
        self.hydrogen_mass = cuds.classes.Mass()
        self.hydrogen1.add(self.hydrogen_mass)
        self.hydrogen2.add(self.hydrogen_mass)

        self.water_molecule_cuds.add(self.oxygen,
                                     self.hydrogen1,
                                     self.hydrogen2)
        self.e.add(self.water_molecule_cuds)

    def test_find_root(self):
        self.assertTrue(find_cuds(self.e.uid, self.e).uid == self.e.uid,
                        "Root should have been found.")

    def test_find_first_level_child(self):
        # Water molecule
        found_el = find_cuds(self.water_molecule_cuds.uid, self.e)
        self.assertTrue(found_el.uid == self.water_molecule_cuds.uid,
                        "Second level element should have been found.")

    def test_find_second_level_children(self):
        # Oxygen
        found_el = find_cuds(self.oxygen.uid, self.e)
        self.assertTrue(found_el.uid == self.oxygen.uid,
                        "Second level element should have been found.")
        # Hydrogen 1
        found_el = find_cuds(self.hydrogen1.uid, self.e)
        self.assertTrue(found_el.uid == self.hydrogen1.uid,
                        "Second level element should have been found.")
        # Hydrogen 2
        found_el = find_cuds(self.hydrogen2.uid, self.e)
        self.assertTrue(found_el.uid == self.hydrogen2.uid,
                        "Second level element should have been found.")

    def test_find_third_level_children(self):
        # Oxygen mass
        found_el = find_cuds(self.oxygen_mass.uid, self.e)
        self.assertTrue(found_el.uid == self.oxygen_mass.uid,
                        "Third level element should have been found.")
        # Hydrogen mass
        found_el = find_cuds(self.hydrogen_mass.uid, self.e)
        self.assertTrue(found_el.uid == self.hydrogen_mass.uid,
                        "Third level element should have been found.")

    def test_find_a_nonexistent_element(self):
        dummy_uuid = UUID
        found_el = find_cuds(dummy_uuid, self.e)
        self.assertTrue(True if found_el is None else False,
                        "There should be no element found.")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeleteCUDS)
    unittest.TextTestRunner(verbosity=2).run(suite)
