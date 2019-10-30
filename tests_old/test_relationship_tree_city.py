# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import cuds.classes
from cuds.classes.relationship_tree import RelationshipTree


class TestRelationshipTree(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation(self):
        """
        Tests the instantiation and type of the objects
        """
        tree = RelationshipTree(cuds.classes.IsInhabitantOf)
        self.assertEqual(tree.root_relationship, cuds.classes.IsInhabitantOf)
        self.assertEqual(dict(), tree.children)

    def test_add(self):
        """Test adding relationships to the tree."""
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.Encloses)
        tree.add(cuds.classes.IsPartOf)
        tree.add(cuds.classes.IsInhabitantOf)
        tree.add(cuds.classes.HasInhabitant)
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
        """Test removing relationships from the tree"""
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.Encloses)
        tree.add(cuds.classes.IsPartOf)
        tree.add(cuds.classes.IsInhabitantOf)
        tree.add(cuds.classes.HasInhabitant)
        tree.add(cuds.classes.ActiveRelationship)
        tree.add(cuds.classes.IsEnclosedBy)
        tree.add(cuds.classes.HasPart)
        tree.add(cuds.classes.PassiveRelationship)

        tree.remove(cuds.classes.ActiveRelationship)
        tree.remove(cuds.classes.Encloses)

        self.assertEqual(set([cuds.classes.HasInhabitant,
                              cuds.classes.HasPart,
                              cuds.classes.PassiveRelationship]),
                         set(tree.children.keys()))

    def test_get_subrelations(self):
        """Test getting subrelationships from the tree."""
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.Encloses)
        tree.add(cuds.classes.IsPartOf)
        tree.add(cuds.classes.IsInhabitantOf)
        tree.add(cuds.classes.HasInhabitant)
        tree.add(cuds.classes.ActiveRelationship)
        tree.add(cuds.classes.IsEnclosedBy)
        tree.add(cuds.classes.HasPart)
        tree.add(cuds.classes.PassiveRelationship)

        self.assertEqual(set([cuds.classes.ActiveRelationship,
                              cuds.classes.Encloses,
                              cuds.classes.HasPart,
                              cuds.classes.HasInhabitant]),
                         tree.get_subrelationships(
                             cuds.classes.ActiveRelationship))
        tree.remove(cuds.classes.ActiveRelationship)
        self.assertEqual(set([cuds.classes.Encloses,
                              cuds.classes.HasPart,
                              cuds.classes.HasInhabitant]),
                         tree.get_subrelationships(
                             cuds.classes.ActiveRelationship))

    def test_contains(self):
        """Test getting subrelationships from the tree."""
        tree = RelationshipTree(cuds.classes.Relationship)
        tree.add(cuds.classes.HasInhabitant)
        tree.add(cuds.classes.HasPart)

        self.assertTrue(tree.contains(cuds.classes.Relationship))
        self.assertTrue(tree.contains(cuds.classes.ActiveRelationship))
        self.assertTrue(tree.contains(cuds.classes.Encloses))
        self.assertTrue(tree.contains(cuds.classes.HasInhabitant))
        self.assertTrue(tree.contains(cuds.classes.HasPart))

        self.assertFalse(tree.contains(cuds.classes.PassiveRelationship))
        self.assertFalse(tree.contains(cuds.classes.IsEnclosedBy))
        self.assertFalse(tree.contains(cuds.classes.IsInhabitantOf))
        self.assertFalse(tree.contains(cuds.classes.IsPartOf))


if __name__ == '__main__':
    unittest.main()
