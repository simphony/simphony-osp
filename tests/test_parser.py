import unittest2 as unittest
import osp.core
from osp.core import ONTOLOGY_INSTALLER, cuba

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    from osp.core.namespaces import city

try:
    from osp.core import parser_test as ONTO
except ImportError:
    ONTO = ONTOLOGY_INSTALLER.parser.parse(
        "osp/core/ontology/yml/parser_test.ontology.yml"
    )


class TestParser(unittest.TestCase):

    def test_ontology_namespace_registry(self):
        """Test the namespace registry"""
        self.assertEqual(
            ONTOLOGY_INSTALLER.namespace_registry.cuba.name,
            "cuba"
        )
        self.assertEqual(
            ONTOLOGY_INSTALLER.namespace_registry["city"].name,
            "city"
        )
        self.assertEqual(
            ONTOLOGY_INSTALLER.namespace_registry.get_main_namespace().name,
            "cuba"
        )

    def test_ontology_namespace(self):
        """Test the namespaces"""
        cuba = ONTOLOGY_INSTALLER.namespace_registry.cuba
        self.assertEqual(
            cuba.relationship.name,
            "relationship"
        )
        self.assertEqual(
            cuba["ENTITY"].name,
            "ENTITY"
        )
        all_names = [x.name for x in cuba]
        self.assertEqual(
            set(all_names),
            {"ENTITY", "relationship", "activeRelationship",
             "WRAPPER", "ATTRIBUTE",
             "passiveRelationship", "NOTHING", "FILE", "PATH"}
        )

    def test_subclass_check(self):
        """ Test subclass and superclass check"""
        city = ONTOLOGY_INSTALLER.namespace_registry.city
        self.assertTrue(city.city.is_subclass_of(city.PopulatedPlace))
        self.assertTrue(city.PopulatedPlace.is_superclass_of(city.city))
        self.assertFalse(city.city.is_superclass_of(city.PopulatedPlace))
        self.assertFalse(city.PopulatedPlace.is_subclass_of(city.city))
        self.assertTrue(city.city.is_subclass_of(city.city))
        self.assertTrue(city.city.is_superclass_of(city.city))

    def test_ontology_entity(self):
        """Test the ontology entities"""
        Citizen = osp.core.city.Citizen
        Person = osp.core.city.Person
        LivingBeing = osp.core.city.LivingBeing
        Entity = osp.core.cuba.Class

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
        Citizen = osp.core.city.Citizen
        Name = osp.core.city.name
        Age = osp.core.city.age

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
        HasPart = osp.core.city.hasPart
        IsPartOf = osp.core.city.isPartOf
        ActiveRelationship = osp.core.cuba.activeRelationship
        Relationship = osp.core.cuba.relationship
        PassiveRelationship = osp.core.cuba.passiveRelationship
        self.assertEqual(HasPart.inverse, IsPartOf)
        self.assertEqual(IsPartOf.inverse, HasPart)
        self.assertEqual(ActiveRelationship.inverse, PassiveRelationship)
        self.assertEqual(PassiveRelationship.inverse, ActiveRelationship)
        self.assertEqual(PassiveRelationship.direct_superclasses,
                         [Relationship])
        self.assertEqual(HasPart.characteristics, ["transitive"])
        self.assertTrue(HasPart.is_transitive)
        self.assertFalse(HasPart.is_symmetric)
        self.assertRaises(AttributeError, getattr, HasPart, "is_cool")
        self.assertRaises(AttributeError, getattr, HasPart, "cool")

    def test_ontology_attributes(self):
        """Test the ontology values"""
        self.assertEqual(osp.core.cuba.attribute.datatype, "UNDEFINED")
        self.assertEqual(osp.core.city.Number.datatype, "INT")
        self.assertEqual(osp.core.city.name.datatype, "UNDEFINED")
        self.assertEqual(osp.core.city.coordinates.datatype, "VECTOR:INT:2")
        self.assertEqual(osp.core.city.numSteps.datatype, "INT")

    def test_multiple_inheritance(self):
        """Test corner cases of multiple inheritance"""
        self.assertEqual(ONTO.ClassC.attributes, {ONTO.attributeA: None})
        self.assertEqual(ONTO.ClassD.attributes,
                         {ONTO.attributeA: "DEFAULT_D"})
        self.assertEqual(ONTO.attributeC.datatype, "UNDEFINED")
        self.assertEqual(ONTO.attributeD.datatype, "FLOAT")

    def test_parse_class_expressions(self):
        """Test the parsing of class expressions"""
        self.assertEqual(
            len(ONTO.relationship_B.domain_expressions), 2
        )
        self.assertEqual(
            ONTO.relationship_B.domain_expressions[0].operator, "and"
        )
        self.assertEqual(
            ONTO.relationship_B.domain_expressions[1].operator, "or"
        )
        self.assertEqual(
            ONTO.relationship_B.domain_expressions[1].operands,
            [ONTO.ClassA, ONTO.ClassB]
        )
        self.assertEqual(
            len(ONTO.relationship_B.domain_expressions[0].operands), 2
        )
        self.assertEqual(
            ONTO.relationship_B.domain_expressions[0].operands[0],
            ONTO.ClassC
        )
        self.assertEqual(
            ONTO.relationship_B.domain_expressions[0].operands[1].operator,
            "not"
        )
        self.assertEqual(
            ONTO.relationship_B.domain_expressions[0].operands[1].operands[0],
            ONTO.ClassD
        )
        self.assertEqual(
            len(ONTO.relationship_B.range_expressions), 1
        )
        self.assertEqual(
            ONTO.relationship_B.range_expressions[0].relationship,
            ONTO.relationship_A
        )
        self.assertEqual(
            ONTO.relationship_B.range_expressions[0].range,
            ONTO.ClassA
        )
        self.assertEqual(
            ONTO.relationship_B.range_expressions[0].cardinality, "some"
        )
        self.assertEqual(
            ONTO.relationship_B.range_expressions[0].exclusive, True
        )

    def test_inverses(self):
        """ Test if missing inverses and active + passive relationships
        have been added"""
        self.assertIs(
            ONTO.relationship_A.inverse,
            ONTO.relationship_C
        )
        self.assertIs(
            ONTO.relationship_A,
            ONTO.relationship_C.inverse
        )
        self.assertIs(
            ONTO.relationship_B.inverse,
            ONTO.INVERSE_OF_relationship_B
        )
        self.assertIs(
            ONTO.relationship_B,
            ONTO.INVERSE_OF_relationship_B.inverse
        )
        # created inverse
        self.assertEqual(
            ONTO.INVERSE_OF_relationship_B.direct_superclasses,
            [ONTO.relationship_C, cuba.passiveRelationship]
        )

        # active and passive
        self.assertIn(
            cuba.activeRelationship,
            ONTO.relationship_A.direct_superclasses
        )
        self.assertIn(
            cuba.passiveRelationship,
            ONTO.relationship_C.direct_superclasses
        )

        self.assertIn(
            ONTO.relationship_A,
            cuba.activeRelationship.direct_subclasses,
        )
        self.assertIn(
            ONTO.relationship_C,
            cuba.passiveRelationship.direct_subclasses,
        )

        self.assertIn(
            cuba.activeRelationship,
            ONTO.relationship_B.direct_superclasses
        )
        self.assertIn(
            cuba.passiveRelationship,
            ONTO.INVERSE_OF_relationship_B.direct_superclasses
        )

        self.assertIn(
            ONTO.relationship_B,
            cuba.activeRelationship.direct_subclasses,
        )
        self.assertIn(
            ONTO.INVERSE_OF_relationship_B,
            cuba.passiveRelationship.direct_subclasses,
        )


if __name__ == '__main__':
    unittest.main()
