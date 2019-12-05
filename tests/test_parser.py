# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import osp.core
from osp.core import ONTOLOGY_INSTALLER

try:
    from osp.core import PARSER_TEST as ONTO
except ImportError:
    ONTO = ONTOLOGY_INSTALLER.parser.parse(
        "osp/core/ontology/yml/ontology.parser_test.yml"
    )


class TestParser(unittest.TestCase):

    def test_ontology_namespace_registry(self):
        """Test the namespace registry"""
        self.assertEqual(
            ONTOLOGY_INSTALLER.namespace_registry.CUBA.name,
            "CUBA"
        )
        self.assertEqual(
            ONTOLOGY_INSTALLER.namespace_registry["CITY"].name,
            "CITY"
        )
        self.assertEqual(
            ONTOLOGY_INSTALLER.namespace_registry.get_main_namespace().name,
            "CUBA"
        )

    def test_ontology_namespace(self):
        """Test the namespaces"""
        CUBA = ONTOLOGY_INSTALLER.namespace_registry.CUBA
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
             "WRAPPER", "ATTRIBUTE", "INVERSE_OF_RELATIONSHIP",
             "INVERSE_OF_ACTIVE_RELATIONSHIP", "NOTHING"}
        )

    def test_subclass_check(self):
        """ Test subclass and superclass check"""
        CITY = ONTOLOGY_INSTALLER.namespace_registry.CITY
        self.assertTrue(CITY.CITY.is_subclass_of(CITY.POPULATED_PLACE))
        self.assertTrue(CITY.POPULATED_PLACE.is_superclass_of(CITY.CITY))
        self.assertFalse(CITY.CITY.is_superclass_of(CITY.POPULATED_PLACE))
        self.assertFalse(CITY.POPULATED_PLACE.is_subclass_of(CITY.CITY))
        self.assertTrue(CITY.CITY.is_subclass_of(CITY.CITY))
        self.assertTrue(CITY.CITY.is_superclass_of(CITY.CITY))

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

    def test_ontology_attributes(self):
        """Test the ontology values"""
        self.assertEqual(osp.core.CUBA.ATTRIBUTE.datatype, "UNDEFINED")
        self.assertEqual(osp.core.CITY.NUMBER.datatype, "INT")
        self.assertEqual(osp.core.CITY.NAME.datatype, "UNDEFINED")
        self.assertEqual(osp.core.CITY.COORDINATES.datatype, "VECTOR:2")
        self.assertEqual(osp.core.CITY.NUM_STEPS.datatype, "INT")

    def test_multiple_inheritance(self):
        """Test corner cases of multiple inheritance"""
        self.assertEqual(ONTO.ENTITY_C.attributes, {ONTO.ATTRIBUTE_A: None})
        self.assertEqual(ONTO.ENTITY_D.attributes,
                         {ONTO.ATTRIBUTE_A: "DEFAULT_D"})
        self.assertEqual(ONTO.ATTRIBUTE_C.datatype, "UNDEFINED")
        self.assertEqual(ONTO.ATTRIBUTE_D.datatype, "FLOAT")

    def test_parse_class_expressions(self):
        """Test the parsing of class expressions"""
        self.assertEqual(
            len(ONTO.RELATIONSHIP_B.domain_expressions), 2
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.domain_expressions[0].operator, "and"
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.domain_expressions[1].operator, "or"
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.domain_expressions[1].operands,
            [ONTO.ENTITY_A, ONTO.ENTITY_B]
        )
        self.assertEqual(
            len(ONTO.RELATIONSHIP_B.domain_expressions[0].operands), 2
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.domain_expressions[0].operands[0],
            ONTO.ENTITY_C
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.domain_expressions[0].operands[1].operator,
            "not"
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.domain_expressions[0].operands[1].operands[0],
            ONTO.ENTITY_D
        )
        self.assertEqual(
            len(ONTO.RELATIONSHIP_B.range_expressions), 1
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.range_expressions[0].relationship,
            ONTO.RELATIONSHIP_A
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.range_expressions[0].range,
            ONTO.ENTITY_A
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.range_expressions[0].cardinality, "some"
        )
        self.assertEqual(
            ONTO.RELATIONSHIP_B.range_expressions[0].exclusive, True
        )


if __name__ == '__main__':
    unittest.main()
