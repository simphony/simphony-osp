# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod
from cuds.generator.settings import get_parsed_settings
import yaml

VERSION_KEY = "VERSION"  # TODO
ONTOLOGY_MODE_KEY = "ONTOLOGY_MODE"  # TODO
ONTOLOGY_KEY = "CUDS_ONTOLOGY"
ROOT_RELATIONSHIP = "RELATIONSHIP"
ROOT_VALUE = "VALUE"

DEFINITION_KEY = "definition"
PARENTS_KEY = "parents"
INVERSE_KEY = "inverse"  # TODO
DEFAULT_REL_KEY = "default_rel"  # TODO
ATTRIBUTES_KEY = "attributes"
RESTRICTIONS_KEY = "restrictions"  # TODO
DATATYPE_KEY = "datatype"
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

    def __init__(self, filename):
        """
        Constructor. Sets the filename.

        :param filename: name of the YAML file with the ontology
        """
        self._filename = filename
        self._ontology = None
        self._parsed_settings = {}
        self.parse()

    def parse(self):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        with open(self._filename, 'r') as stream:
            try:
                yaml_doc = yaml.safe_load(stream)
                self._parsed_settings = get_parsed_settings(yaml_doc)
                self._ontology = Ontology(yaml_doc[ONTOLOGY_KEY])
                self._ontology.load()
            except yaml.YAMLError as exc:
                print(exc)

    def get_parsed_settings(self):
        return self._parsed_settings

    def get_ontology(self):
        return self._ontology


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
        parent_names = yaml_def[PARENTS_KEY]
        for p in parent_names:
            self._load_entity(p)
        parents = [self._entities[p] for p in parent_names]
        entity = self._create_entity(entity_name, parents, yaml_def)
        self._entities[entity_name] = entity
        for p in parents:
            p._add_child(entity)

    def _create_entity(self, entity_name, parents, yaml_def):
        """Create an entity object

        :param entity_name: The name of the entity
        :type entity_name: str
        :param parents: The parents
        :type parents: List[OntologyEntity]
        :param yaml_def: The yaml definition of the entity
        :type yaml_def: Dict[Any]
        """
        superclasses = {entity_name}
        for p in parents:
            superclasses |= p.get_superclasses()
        if ROOT_VALUE in superclasses:
            Class = OntologyValue
        elif ROOT_RELATIONSHIP in superclasses:
            Class = OntologyRelationship
        else:
            Class = OntologyClass
        return Class(name=entity_name,
                     parents=parents,
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


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, name, parents, yaml_def):
        """Initialize the ontology entity

        :param name: The name of the entity
        :type name: str
        :param parents: The parents of the entity
        :type parents: List[OntologyEntity]
        :param yaml_def: The yaml definition of the entity
        :type yaml_def: dict[Any]
        """
        self._name = name
        self._children = set()
        self._parents = parents
        self._definition = yaml_def[DEFINITION_KEY]

    def get_direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return self._parents

    def get_direct_subclasses(self):
        """Get the direct subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return self.children

    def get_subclasses(self):
        """Get the subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        result = {self}
        result |= self._children
        for c in self._children:
            result |= c.get_subclasses()
        return result

    def get_superclasses(self):
        """Get the superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        result = {self}
        result |= self._parents
        for p in self._parents:
            result |= p.get_superclasses()
        return result

    def get_definition(self):
        """Get the definition of the entity

        :return: The definition of the entity
        :rtype: str
        """
        if self._definition:
            return self._definition
        return "To Be Determined"

    def _add_child(self, child):
        """Add a subclass to the entity

        :param child: The subclass to add
        :type child: OntologyEntity
        """
        self._children.add(child)


class OntologyValue(OntologyEntity):
    def __init__(self, name, parents, yaml_def):
        super().__init__(name, parents, yaml_def)
        self._datatype = None
        if DATATYPE_KEY in yaml_def:
            self._datatype = yaml_def[DATATYPE_KEY]

    def get_datatype(self):
        """Get the datatype of the value

        :return: The datatype of the ontology value
        :rtype: str
        """
        if self._datatype is not None:
            return self._datatype  # datatype is defined

        # check for inherited datatype
        datatype = None
        for p in self.get_direct_superclasses():
            parent_datatype = p.get_datatype()
            if datatype is not None and parent_datatype is not None:
                return "UNDEFINED"  # conflicting datatypes of parents
            datatype = datatype or parent_datatype

        if datatype is None:
            return "UNDEFINED"  # undefined datatype
        return datatype


class OntologyRelationship(OntologyEntity):
    def __init__(self, name, parents, yaml_def):
        super().__init__(name, parents, yaml_def)


class OntologyClass(OntologyEntity):
    def __init__(self, name, parents, definition):
        super().__init__(name, parents, definition)
        self._attributes = dict()

    def get_attributes(self):
        """Get all (inherited + own) the attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        result = self.get_inherited_attributes()
        result.update(self.get_own_attributes())
        return result

    def get_own_attributes(self):
        """Get all the own attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        return self._attributes

    def get_inherited_attributes(self):
        """Get all the inherited attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        result = dict()
        superclasses = self.get_superclasses()
        for c in superclasses:
            if c is self:
                continue
            result.update(c.get_own_attributes())
        return result

    def _add_attribute(self, attribute, default):
        """Add an attribute to the class

        :param attribute: The attribute to add
        :type attribute: OntologyValue
        """
        self._attributes[attribute] = default
