# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, namespace, name, superclasses, definition):
        """Initialize the ontology entity

        :param namespace: The namespace of the entity
        :type namespace: OntologyNamespace
        :param name: The name of the entity
        :type name: str
        :param superclasses: The superclasses of the entity
        :type superclasses: List[OntologyEntity]
        :param definition: The defintion of the entity
        :type definition: str
        """
        self._name = name
        self._namespace = namespace
        self._subclasses = list()
        self._superclasses = list(superclasses)
        self._definition = definition

    def __str__(self):
        return "%s.%s" % (self.namespace.name, self._name)

    def __repr__(self):
        return "<%s %s.%s>" % (
            self.__class__.__name__,
            self.namespace.name,
            self._name
        )

    @property
    def name(self):
        """Get the name of the entity"""
        return self._name

    @property
    def tblname(self):
        return "%s___%s" % (self.namespace.name, self._name)

    @property
    def namespace(self):
        """Get the name of the entity"""
        return self._namespace

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: List[OntologyEntity]
        """
        return self._superclasses

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        return self._subclasses

    @property
    def subclasses(self):
        """Get the subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        subclasses = [self]
        for p in self._subclasses:
            subclasses.extend(p.subclasses)
        result = list()
        for i, p in enumerate(subclasses):
            if p not in result:
                result.append(p)
        return result

    @property
    def superclasses(self):
        """Get the superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        superclasses = [self]
        for p in self._superclasses:
            superclasses.extend(p.superclasses)
        result = list()
        for i, p in enumerate(superclasses):
            if p not in superclasses[i + 1:]:
                result.append(p)
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

    def is_subclass_of(self, other):
        """Subclass check.

        :param other: Check if self is a subclass of this entity.
        :type other: OntologyEntity
        :return: Whether self is a subclass of other.
        :rtype: bool
        """
        return self in other.subclasses

    def is_superclass_of(self, other):
        """Superclass check.

        :param other: Check if self is a superclass of this entity.
        :type other: OntologyEntity
        :return: Whether self is a superclass of other.
        :rtype: bool
        """
        return self in other.superclasses

    def _add_subclass(self, subclass):
        """Add a subclass to the entity

        :param subclass: The subclass to add
        :type subclass: OntologyEntity
        """
        if subclass not in self._subclasses:
            self._subclasses.append(subclass)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
