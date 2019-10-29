# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, name, superclasses, definition):
        """Initialize the ontology entity

        :param name: The name of the entity
        :type name: str
        :param superclasses: The superclasses of the entity
        :type superclasses: List[OntologyEntity]
        :param definition: The defintion of the entity
        :type definition: str
        """
        self._name = name
        self._subclasses = set()
        self._superclasses = set(superclasses)
        self._definition = definition

    @property
    def name(self):
        """Get the name of the entity"""
        return self._name

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return self._superclasses

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return self.children

    @property
    def subclasses(self):
        """Get the subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        result = {self}
        result |= self._subclasses
        for c in self._subclasses:
            result |= c.get_subclasses()
        return result

    @property
    def superclasses(self):
        """Get the superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]  # TODO MRO
        """
        result = {self}
        result |= self._superclasses
        for p in self._superclasses:
            result |= p.superclasses
        return result

    @property
    def definition(self):
        """Get the definition of the entity

        :return: The definition of the entity
        :rtype: str
        """
        if self._definition:
            return self._definition
        return "To Be Determined"

    def _add_subclass(self, subclass):
        """Add a subclass to the entity

        :param subclass: The subclass to add
        :type subclass: OntologyEntity
        """
        self._subclasses.add(subclass)
