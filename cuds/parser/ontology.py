# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.parser import (
    SUPERCLASSES_KEY, ROOT_VALUE, ROOT_RELATIONSHIP, ATTRIBUTES_KEY
)
from cuds.parser.ontology_class import OntologyClass
from cuds.parser.ontology_relationship import OntologyRelationship
from cuds.parser.ontology_value import OntologyValue


class Ontology():
    def __init__(self, yaml_doc):
        self._yaml_doc = yaml_doc
        self._entities = dict()

    def load(self):
        """Load the ontology"""
        for entity_name in self._yaml_doc:
            self._load_entity(entity_name)
        for entity_name in self._yaml_doc:
            self._add_attributes(entity_name)

    def _load_entity(self, entity_name):
        """Load an entity into the registry

        :param entity_name: The name of the entity to load.
        :type entity_name: str
        """
        if entity_name in self._entities:
            return
        yaml_def = self._yaml_doc[entity_name]
        superclass_names = yaml_def[SUPERCLASSES_KEY]
        for p in superclass_names:
            self._load_entity(p)
        superclasses = [self._entities[p] for p in superclass_names]
        entity = self._create_entity(entity_name, superclasses, yaml_def)
        self._entities[entity_name] = entity
        for p in superclasses:
            p._add_child(entity)

    def _create_entity(self, entity_name, superclasses, yaml_def):
        """Create an entity object

        :param entity_name: The name of the entity
        :type entity_name: str
        :param superclasses: The superclasses
        :type superclasses: List[OntologyEntity]
        :param yaml_def: The yaml definition of the entity
        :type yaml_def: Dict[Any]
        """
        superclasses = {entity_name}
        for p in superclasses:
            superclasses |= p.get_superclasses()
        if ROOT_VALUE in superclasses:
            Class = OntologyValue
        elif ROOT_RELATIONSHIP in superclasses:
            Class = OntologyRelationship
        else:
            Class = OntologyClass
        return Class(name=entity_name,
                     superclasses=superclasses,
                     yaml_def=yaml_def)

    def _add_attributes(self, entity_name):
        """Add the attributes to an ontology class

        :param entity_name: The name of the class
        :type entity_name: str
        """
        entity = self._entities[entity_name]
        if not isinstance(entity, OntologyClass):
            return
        attributes = self._yaml_doc[entity_name][ATTRIBUTES_KEY]
        for a in attributes:
            entity._add_attribute(self._entities[a])

    def __getattr__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self.entities.__getitem__(name)

    def __getitem__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self.entities.__getitem__(name)

    def __iter__(self):
        return self._entities.__iter__()

    def __contains__(self, obj):
        return obj in self._entities
