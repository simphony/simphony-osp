# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import yaml


class Parser:
    """
    Class that parses a YAML file and finds information about the entities
    contained.
    """
    ONTOLOGY_KEY = 'CUDS_ONTOLOGY'

    def __init__(self, filename):
        """
        Constructor. Sets the filename.

        :param filename: name of the YAML file with the ontology
        """
        self._filename = filename
        self._ontology = {}
        self.parse()
        self._entities = frozenset(self._ontology.keys())

    def parse(self):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        with open(self._filename, 'r') as stream:
            try:
                self._ontology = yaml.safe_load(stream)[self.ONTOLOGY_KEY]
            except yaml.YAMLError as exc:
                print(exc)

    def get_entities(self):
        """
        Returns the entities in the ontology.

        :return: list(str) of the classes' names in the ontology
        """
        return self._ontology.keys()

    def get_value(self, entity, key):
        """
        Gets the value for a specific entity and key.

        :param entity: name of the entity in the ontology
        :param key: key for the value
        :return: value for that entity and key
        """
        try:
            value = self._ontology[entity][key]
        except KeyError as ke:
            message = 'Entity {} has no attribute called {}.'
            raise KeyError(message.format(entity, key)) from ke
        return value

    def get_definition(self, entity):
        """
        Getter for the definition associated to an entity.

        :param entity: entity whose definition to return
        :return: str with the definition
        """
        definition = self.get_value(entity, 'definition')
        return definition if definition is not None else "To Be Determined"

    def get_parent(self, entity):
        """
        Computes the parent of an entity, if there is one.

        :param entity: entity whose parent to return
        :return: name of the parent class
        :raises KeyError: the queried entity does not exist
        """
        try:
            parent = self.get_value(entity, 'parent')
        except KeyError:
            message = '{!r} does not exist. Try again.'
            raise KeyError(message.format(entity))
        # Erase "CUBA." prefix
        parent = "" if parent is None else parent.replace("CUBA.", "")
        return parent

    def get_cuba_attributes_filtering(self, entity, not_relevant):
        """
        Filters the attributes to the CUBA ones and returns the contained info.

        :param entity: name of the entity whose attributes are wanted
        :param not_relevant: set of attributes to skip
        :return: dictionary with the attributes that start with CUBA.
        """
        cuba_attributes = {}
        for key in self._ontology[entity].keys():
            if key.startswith("CUBA."):
                if key.replace("CUBA.", "") not in not_relevant:
                    cuba_attributes[key] = self._ontology[entity][key]
        return cuba_attributes

    def get_attributes(self, entity, inheritance=True):
        """
        Computes a list of attributes of an entity.
        If inheritance is set, it will add the attributes from the parents.

        :param entity: entity that has the wanted attributes
        :param inheritance: whether inherited attributes should be added or not
        :return: sorted list with the names of the attributes
        """
        attributes = self.get_own_attributes(entity)
        if inheritance:
            inherited = self.get_inherited_attributes(entity)
            attributes.update(inherited)
        return attributes

    def get_own_attributes(self, entity):
        """
        Creates a list with the attributes particular to an entity.

        :param entity: entity whose own attributes should be computed
        :return: list of the names of the attributes
        """
        own_attributes = {}
        for key, val in self._ontology[entity].items():
            key = key.replace("CUBA.", "")
            if key in self._entities:
                own_attributes[key.lower()] = val
        return own_attributes

    def get_inherited_attributes(self, entity):
        """
        Creates a list with the attributes obtained through inheritance.

        :param entity: entity whose inherited attributes should be computed
        :return: list of the names of the inherited attributes
        """
        ancestors = self.get_ancestors(entity)
        attributes = {}
        for ancestor in ancestors:
            attributes_ancestor = self.get_own_attributes(ancestor)
            if attributes_ancestor:
                attributes.update(attributes_ancestor)
        return attributes

    def get_ancestors(self, leaf_entity):
        """
        Computes all the entities above a given one.

        :param leaf_entity: entity at the base
        :return: list(str) with the parent entity and its parent until the root
        """
        ancestors = []
        parent = self.get_parent(leaf_entity)
        while parent != "":
            ancestors.append(parent)
            parent = self.get_parent(parent)
        return ancestors

    def get_descendants(self, root_entity):
        """
        Computes all the entities under a given one.

        :param root_entity: entity at the top
        :return: list(str) with the child entity and its child until the leaf
        """
        descendants = [root_entity]
        for entity in self.get_entities():
            # Set the root_entity to the initial parent for the loop
            parent = entity
            while parent != "":
                parent = self.get_parent(parent)
                if parent in descendants:
                    descendants.append(entity)
                    break
        # Remove the root (only descendants)
        descendants.remove(root_entity)
        return descendants
