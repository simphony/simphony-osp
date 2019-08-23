# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import cuds.classes
from cuds.classes.core.relationship_tree import RelationshipTree


class TestRelationshipTree(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        tree = RelationshipTree(cuds.classes.Inhabits)
        self.assertEqual(tree.root_relationship, cuds.classes.Inhabits)
        self.assertEqual(dict(), tree.children)

    def test_add(self):
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.Encloses)
        tree.add(cuds.classes.IsPartOf)
        tree.add(cuds.classes.Inhabits)
        tree.add(cuds.classes.IsInhabitedBy)
        tree.add(cuds.classes.ActiveRelationship)
        tree.add(cuds.classes.IsEnclosedBy)
        tree.add(cuds.classes.HasPart)
        tree.add(cuds.classes.PassiveRelationship)
        self.assertEqual(set([cuds.classes.ActiveRelationship,
                              cuds.classes.PassiveRelationship]),
                         tree.children.keys())
        active_rel_tree = tree.children[cuds.classes.ActiveRelationship]
        passive_rel_tree = tree.children[cuds.classes.PassiveRelationship]
        self.assertEqual(set([cuds.classes.Encloses]),
                         active_rel_tree.children.keys())
        self.assertEqual(set([cuds.classes.IsEnclosedBy]),
                         passive_rel_tree.children.keys())

    def test_remove(self):
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.Encloses)
        tree.add(cuds.classes.IsPartOf)
        tree.add(cuds.classes.Inhabits)
        tree.add(cuds.classes.IsInhabitedBy)
        tree.add(cuds.classes.ActiveRelationship)
        tree.add(cuds.classes.IsEnclosedBy)
        tree.add(cuds.classes.HasPart)
        tree.add(cuds.classes.PassiveRelationship)

        tree.remove(cuds.classes.ActiveRelationship)
        tree.remove(cuds.classes.Encloses)

        self.assertEqual(set([cuds.classes.IsInhabitedBy,
                              cuds.classes.HasPart,
                              cuds.classes.PassiveRelationship]),
                         set(tree.children.keys()))

    def test_get_subrelations(self):
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.Encloses)
        tree.add(cuds.classes.IsPartOf)
        tree.add(cuds.classes.Inhabits)
        tree.add(cuds.classes.IsInhabitedBy)
        tree.add(cuds.classes.ActiveRelationship)
        tree.add(cuds.classes.IsEnclosedBy)
        tree.add(cuds.classes.HasPart)
        tree.add(cuds.classes.PassiveRelationship)

        self.assertEqual(set([cuds.classes.ActiveRelationship,
                              cuds.classes.Encloses,
                              cuds.classes.HasPart,
                              cuds.classes.IsInhabitedBy]),
                         tree.get_subrelationships(
                             cuds.classes.ActiveRelationship))
        tree.remove(cuds.classes.ActiveRelationship)
        self.assertEqual(set([cuds.classes.Encloses,
                              cuds.classes.HasPart,
                              cuds.classes.IsInhabitedBy]),
                         tree.get_subrelationships(
                             cuds.classes.ActiveRelationship))


if __name__ == '__main__':
    unittest.main()
