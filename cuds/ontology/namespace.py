# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY


class OntologyNamespace():
    def __init__(self, name):
        self._name = name
        self._entities = dict()
        ONTOLOGY_NAMESPACE_REGISTRY.add_namespace(self)

    @property
    def name(self):
        """Get the name of the namespace"""
        return self._name

    def __getattribute__(self, name):
        return super().__getattribute__(name)

    def __getattr__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self.get(name)

    def __getitem__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self.get(name)

    def get(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self.entities.__getitem__(name)

    def __iter__(self):
        """Iterate over the ontology entities in the namespace.

        :return: An iterator over the entities.
        :rtype: Iterator[OntologyEntity]
        """
        return self._entities.__iter__()

    def __contains__(self, obj):
        return obj in self._entities

    def _add_entity(self, entity):
        """Add an entity to the namespace.

        :param entity: The entity to add.
        :type entity: OntologyEntity
        """
        from cuds.ontology.entity import OntologyEntity
        assert isinstance(entity, OntologyEntity)
        self._entities[entity.name] = entity
