# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import yaml
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute

VERSION_KEY = "VERSION"  # TODO
ONTOLOGY_MODE_KEY = "ONTOLOGY_MODE"  # TODO
ONTOLOGY_KEY = "ONTOLOGY"
ROOT_RELATIONSHIP = "RELATIONSHIP"
ROOT_ATTRIBUTE = "ATTRIBUTE"
NAMESPACE_KEY = "NAMESPACE"

DESCRIPTION_KEY = "description"
SUPERCLASSES_KEY = "subclass_of"
INVERSE_KEY = "inverse"
DEFAULT_REL_KEY = "default_rel"
DATATYPE_KEY = "datatype"
ATTRIBUTES_KEY = "attributes"
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

    def __init__(self, namespace_registry=None):
        from osp.core.ontology.namespace_registry import \
            ONTOLOGY_NAMESPACE_REGISTRY

        self._namespace_registry = namespace_registry or \
            ONTOLOGY_NAMESPACE_REGISTRY
        self._filename = None
        self._yaml_doc = None
        self._ontology_namespace = None

    def parse(self, filename):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        from osp.core.ontology.namespace import OntologyNamespace

        if not filename.endswith(".yml"):
            filename = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "yml", "ontology.%s.yml" % filename
            )

        self.__init__()
        self._filename = filename
        with open(self._filename, 'r') as stream:
            self._yaml_doc = yaml.safe_load(stream)
            self._ontology_namespace = OntologyNamespace(
                self._yaml_doc[NAMESPACE_KEY]
            )
            self._namespace_registry._add_namespace(self._ontology_namespace)
            self._parse_ontology()
        return self._ontology_namespace

    def _parse_ontology(self):
        """Parse the entity descriptions."""
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]

        for entity_name in cuds_yaml_doc:
            self._load_entity(entity_name)

        missing_inverse = set()
        for entity in self._ontology_namespace:
            if isinstance(entity, OntologyClass):
                self._add_attributes(entity)
            elif isinstance(entity, OntologyRelationship):
                missing_inverse |= self._set_inverse(entity)
                self._check_default_rel(entity)
            else:
                self._set_datatype(entity)
        for entity in missing_inverse:
            self._create_missing_inverse(entity)

    def _split_name(self, name):
        try:
            return name.split(".")
        except ValueError as e:
            raise ValueError("Reference to entity %s without namespace"
                             % name) from e

    def _load_entity(self, entity_name):
        """Load an entity into the registry

        :param entity_name: The name of the entity to load.
        :type entity_name: str
        """
        if entity_name in self._ontology_namespace:
            return

        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity_name]
        description = None
        if DESCRIPTION_KEY in entity_yaml_doc:
            description = entity_yaml_doc[DESCRIPTION_KEY]

        # load the superclasses first
        superclass_names = entity_yaml_doc[SUPERCLASSES_KEY]
        superclasses = list()
        for p in superclass_names:
            if not isinstance(p, str):
                continue
            namespace, superclass_name = self._split_name(p)
            namespace = self._namespace_registry[namespace]
            if namespace is self._ontology_namespace:
                self._load_entity(superclass_name)
            superclasses.append(namespace[superclass_name])
        entity = self._create_entity(entity_name, superclasses, description)
        self._ontology_namespace._add_entity(entity)
        for p in superclasses:
            p._add_subclass(entity)

    def _create_entity(self, entity_name, superclasses, description):
        """Create an entity object

        :param entity_name: The name of the entity
        :type entity_name: str
        :param description: The description of the entity
        :type yaml_def: str
        """
        superclass_names = {entity_name}
        for p in superclasses:
            superclass_names |= {x.name for x in p.superclasses}
        if ROOT_ATTRIBUTE in superclass_names:
            Class = OntologyAttribute
        elif ROOT_RELATIONSHIP in superclass_names:
            Class = OntologyRelationship
        else:
            Class = OntologyClass
        result = Class(namespace=self._ontology_namespace,
                       name=entity_name,
                       superclasses=superclasses,
                       description=description)
        self._ontology_namespace._add_entity(result)
        return result

    def _add_attributes(self, entity: OntologyClass):
        """Add a attribute to an ontology class

        :param entity: The ontology to add the attributes to
        :type entity: OntologyClass
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        attributes_def = None
        if ATTRIBUTES_KEY in entity_yaml_doc:
            attributes_def = entity_yaml_doc[ATTRIBUTES_KEY]

        if attributes_def is None:
            return

        # Add the attributes one by one
        for attribute_name, default in attributes_def.items():
            attribute_namespace, attribute_name = \
                self._split_name(attribute_name)
            attribute_namespace = self._namespace_registry[attribute_namespace]
            attribute = attribute_namespace[attribute_name]
            entity._add_attribute(attribute, default)

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
            inverse_namespace, inverse_name = self._split_name(inverse_def)
            inverse_namespace = self._namespace_registry[inverse_namespace]
            inverse = inverse_namespace[inverse_name]
            entity._set_inverse(inverse)
            return set()
        return {entity}

    def _create_missing_inverse(self, entity: OntologyRelationship):
        """Create the missing inverse

        :param entity: [description]
        :type entity: OntologyRelationship
        :return: [description]
        :rtype: [type]
        """
        inverse = OntologyRelationship(
            namespace=self._ontology_namespace,
            name="INVERSE_OF_%s" % entity.name,
            superclasses=[self._namespace_registry
                          .get_main_namespace().RELATIONSHIP],
            description="Inverse of %s" % entity.name
        )
        self._ontology_namespace._add_entity(inverse)
        inverse._set_inverse(entity)
        entity._set_inverse(inverse)
        return {inverse}

    def _check_default_rel(self, entity: OntologyRelationship):
        """Check of the given relationship the default
        When it is a default, save that accordingly.

        :param entity: The relationship to check
        :type entity: OntologyRelationship
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]
        if DEFAULT_REL_KEY in entity_yaml_doc \
                and entity_yaml_doc[DEFAULT_REL_KEY]:
            self._ontology_namespace._default_rel = entity

    def _set_datatype(self, entity: OntologyAttribute):
        """Set the datatype of a attribute

        :param entity: The attribute to set the datatype of
        :type entity: OntologyAttribute
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        datatype_def = None
        if DATATYPE_KEY in entity_yaml_doc:
            datatype_def = entity_yaml_doc[DATATYPE_KEY]

        if datatype_def is not None:
            entity._set_datatype(datatype_def)
