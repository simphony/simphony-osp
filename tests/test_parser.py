# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import osp.core
from osp.core.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY


class TestParser(unittest.TestCase):

    def test_ontology_namespace_registry(self):
        """Test the namespace registry"""
        self.assertEqual(
            ONTOLOGY_NAMESPACE_REGISTRY.CUBA.name,
            "CUBA"
        )
        self.assertEqual(
            ONTOLOGY_NAMESPACE_REGISTRY["CITY"].name,
            "CITY"
        )
        self.assertEqual(ONTOLOGY_NAMESPACE_REGISTRY.get_main_namespace().name,
                         "CUBA")

    def test_ontology_namespace(self):
        """Test the namespaces"""
        CUBA = ONTOLOGY_NAMESPACE_REGISTRY.CUBA
        self.assertEqual(
            CUBA.RELATIONSHIP.name,
            "RELATIONSHIP"
        )
        self.assertEqual(
            CUBA["ENTITY"].name,
            "ENTITY"
        )
        all_names = [x.name for x in CUBA]
        self.assertEqual(
            set(all_names),
            {"ENTITY", "RELATIONSHIP", "ACTIVE_RELATIONSHIP",
             "WRAPPER", "VALUE", "INVERSE_OF_RELATIONSHIP",
             "INVERSE_OF_ACTIVE_RELATIONSHIP"}
        )

    def test_ontology_entity(self):
        """Test the ontology entities"""
        Citizen = osp.core.CITY.CITIZEN
        Person = osp.core.CITY.PERSON
        LivingBeing = osp.core.CITY.LIVING_BEING
        Entity = osp.core.CUBA.ENTITY

        self.assertEqual(
            Person.direct_superclasses,
            [LivingBeing]
        )
        self.assertEqual(
            Person.direct_subclasses,
            [Citizen]
        )
        self.assertEqual(
            Person.superclasses,
            [Person, LivingBeing, Entity]
        )
        self.assertEqual(
            Person.subclasses,
            [Person, Citizen]
        )

    def test_ontology_class(self):
        """Test the ontology relationships"""
        Citizen = osp.core.CITY.CITIZEN
        Name = osp.core.CITY.NAME
        Age = osp.core.CITY.AGE

        self.assertEqual(
            Citizen.attributes,
            {Name: "John Smith", Age: 25}
        )
        self.assertEqual(
            Citizen.own_attributes,
            dict()
        )

    def test_ontology_relationship(self):
        """Test the ontology relationship"""
        HasPart = osp.core.CITY.HAS_PART
        IsPartOf = osp.core.CITY.IS_PART_OF
        ActiveRelationship = osp.core.CUBA.ACTIVE_RELATIONSHIP
        Relationship = osp.core.CUBA.RELATIONSHIP
        PassiveRelationship = osp.core.CUBA.INVERSE_OF_ACTIVE_RELATIONSHIP
        self.assertEqual(HasPart.inverse, IsPartOf)
        self.assertEqual(IsPartOf.inverse, HasPart)
        self.assertEqual(ActiveRelationship.inverse, PassiveRelationship)
        self.assertEqual(PassiveRelationship.inverse, ActiveRelationship)
        self.assertEqual(PassiveRelationship.direct_superclasses,
                         [Relationship])

    def test_ontology_values(self):
        """Test the ontology values"""
        self.assertEqual(osp.core.CUBA.VALUE.datatype, "UNDEFINED")
        self.assertEqual(osp.core.CITY.NUMBER.datatype, "INT")
        self.assertEqual(osp.core.CITY.NAME.datatype, "UNDEFINED")
        self.assertEqual(osp.core.CITY.COORDINATES.datatype, "VECTOR:2")
        self.assertEqual(osp.core.CITY.NUM_STEPS.datatype, "INT")


if __name__ == '__main__':
    unittest.main()