# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod
from cuds.parser import DEFINITION_KEY


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, name, superclasses, yaml_def):
        """Initialize the ontology entity

        :param name: The name of the entity
        :type name: str
        :param superclasses: The superclasses of the entity
        :type superclasses: List[OntologyEntity]
        :param yaml_def: The yaml definition of the entity
        :type yaml_def: dict[Any]
        """
        self._name = name
        self._children = set()
        self._superclasses = superclasses
        self._definition = yaml_def[DEFINITION_KEY]

    def get_direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return self._superclasses

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
        result |= self._superclasses
        for p in self._superclasses:
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
