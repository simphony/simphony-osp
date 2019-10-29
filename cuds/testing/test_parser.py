# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import unittest2 as unittest
from cuds.ontology.parser import Parser
from cuds.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY


class TestParser(unittest.TestCase):

    def setUp(self):
        parser = Parser()
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, "..", "ontology", "yml", "ontology.city.yml")
        parser.parse(path)

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
        """Test the ontology entites"""
        Citizen = ONTOLOGY_NAMESPACE_REGISTRY.CITY.CITIZEN
        Person = ONTOLOGY_NAMESPACE_REGISTRY.CITY.PERSON
        LivingBeing = ONTOLOGY_NAMESPACE_REGISTRY.CITY.LIVING_BEING
        Entity = ONTOLOGY_NAMESPACE_REGISTRY.CUBA.ENTITY

        self.assertEqual(
            Person.direct_superclasses,
            {LivingBeing}
        )
        self.assertEqual(
            Person.direct_subclasses,
            {Citizen}
        )
        self.assertEqual(
            Person.superclasses,
            {Person, LivingBeing, Entity}
        )
        self.assertEqual(
            Person.subclasses,
            {Person, Citizen}
        )

    def test_ontology_relationship(self):
        """Test the ontology relationships"""
        


if __name__ == '__main__':
    unittest.main()
