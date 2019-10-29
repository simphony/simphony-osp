# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY
from cuds.ontology.namespace import OntologyNamespace
from cuds.ontology.oclass import OntologyClass
from cuds.ontology.relationship import OntologyRelationship
from cuds.ontology.value import OntologyValue
import yaml

VERSION_KEY = "VERSION"  # TODO
ONTOLOGY_MODE_KEY = "ONTOLOGY_MODE"  # TODO
ONTOLOGY_KEY = "CUDS_ONTOLOGY"
ROOT_RELATIONSHIP = "RELATIONSHIP"
ROOT_VALUE = "VALUE"
NAMESPACE_KEY = "NAMESPACE"

DEFINITION_KEY = "definition"
SUPERCLASSES_KEY = "subclass_of"
INVERSE_KEY = "inverse"
DEFAULT_REL_KEY = "default_rel"  # TODO
DATATYPE_KEY = "datatype"
VALUES_KEY = "values"
RESTRICTIONS_KEY = "restrictions"  # TODO
DISJOINTS_KEY = "disjoints"  # TODO
EQUIVALENT_TO_KEY = "equivalent_to"  # TODO
DOMAIN_KEY = "domain"  # TODO
RANGE_KEY = "range"  # TODO
CHARACTERISTICS_KEY = "characteristics"  # TODO

# class expressions
OR_KEY = "OR"  # TODO
AND_KEY = "AND"  # TODO
NOT_KEY = "NOT"  # TODO
CARDINALITY_KEY = "cardinality"  # TODO
TARGET_KEY = "target"  # TODO
ONLY_KEY = "only"  # TODO


class Parser:
    """
    Class that parses a YAML file and finds information about the entities
    contained.
    """

    def __init__(self):
        self._filename = None
        self._yaml_doc
        self._ontology_namespace = None

    def parse(self, filename):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        self.__init__()
        self._filename = filename
        with open(self._filename, 'r') as stream:
            self._yaml_doc = yaml.safe_load(stream)
            self._ontology_namespace = OntologyNamespace(
                self._yaml_doc[NAMESPACE_KEY]
            )
            self._parse_cuds_ontology()
        return self._ontology_namespace

    def _parse_cuds_ontology(self):
        """Parse the entity definitions."""
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]

        for entity_name in cuds_yaml_doc:
            self._load_entity(entity_name)

        for entity in self._entities.values():
            if isinstance(entity, OntologyClass):
                self._add_values(entity)
            elif isinstance(entity, OntologyRelationship):
                self._set_inverse(entity)
            else:
                self._set_datatype(entity)

    def _load_entity(self, entity_name):
        """Load an entity into the registry

        :param entity_name: The name of the entity to load.
        :type entity_name: str
        """
        if entity_name in self._entities:
            return

        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity_name]
        definition = entity_yaml_doc[DEFINITION_KEY]

        superclass_names = entity_yaml_doc[SUPERCLASSES_KEY]
        superclasses = list()
        for p in superclass_names:
            namespace, superclass_name = p.split(".")
            namespace == ONTOLOGY_NAMESPACE_REGISTRY[namespace]
            if namespace is self._ontology_namespace:
                self._load_entity(superclass_name)
            superclasses.append(namespace[superclass_name])
        entity = self._create_entity(entity_name, superclasses, definition)
        self._ontology_namespace._add_entity(entity)
        for p in superclasses:
            p._add_child(entity)

    def _create_entity(self, entity_name, superclasses, definition):
        """Create an entity object

        :param entity_name: The name of the entity
        :type entity_name: str
        :param definition: The definition of the entity
        :type yaml_def: str
        """
        superclass_names = {entity_name}
        for p in superclasses:
            superclass_names |= {x.name for x in p.superclasses}
        if ROOT_VALUE in superclass_names:
            Class = OntologyValue
        elif ROOT_RELATIONSHIP in superclass_names:
            Class = OntologyRelationship
        else:
            Class = OntologyClass
        return Class(name=entity_name,
                     superclasses=superclasses,
                     definition=definition)

    def _add_values(self, entity: OntologyClass):
        """Add a value to an ontology class

        :param entity: The ontology to add the values to
        :type entity: OntologyClass
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]
        values_def = entity_yaml_doc[VALUES_KEY]

        # Add the values one by one
        for value_name, default in values_def.items():
            value_namespace, value_name = value_name.split(".")
            value_namespace = ONTOLOGY_NAMESPACE_REGISTRY[value_namespace]
            value = value_namespace[value_name]
            entity._add_value(value, default)

    def _set_inverse(self, entity: OntologyRelationship):
        """Set the inverse of the given entity

        :param entity: The ontology relationship to set and inverse.
        :type entity: OntologyRelationship
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        inverse_def = None
        if INVERSE_KEY in entity_yaml_doc:
            inverse_def = entity_yaml_doc[INVERSE_KEY]

        # Inverse is defined
        if inverse_def is not None:
            inverse_namespace, inverse_name = inverse_def.split(".")
            inverse_namespace = ONTOLOGY_NAMESPACE_REGISTRY[inverse_namespace]
            inverse = inverse_namespace[inverse_name]
            entity._set_inverse(inverse)

        # Inverse not defined --> Create one
        else:
            inverse = OntologyRelationship(
                name="INVERSE_OF_%s" % entity.name,
                superclasses=[ONTOLOGY_NAMESPACE_REGISTRY.get_main_namespace
                                                         .RELATIONSHIP],
                defintion="Inverse of %s" % entity.name
            )
            self._ontology_namespace._add_entity(inverse)
            inverse._set_inverse(entity)
            entity._set_inverse(inverse)

    def _set_datatype(self, entity: OntologyValue):
        """Set the datatype of a value

        :param entity: [description]
        :type entity: OntologyValue
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        datatype_def = None
        if DATATYPE_KEY in entity_yaml_doc:
            datatype_def = entity_yaml_doc[DATATYPE_KEY]

        if datatype_def is not None:
            entity._set_datatype(datatype_def)
