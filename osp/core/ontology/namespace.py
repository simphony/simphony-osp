# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


class OntologyNamespace():
    def __init__(self, name):
        self._name = name
        self._entities = dict()
        self._default_rel = None

    @property
    def name(self):
        """Get the name of the namespace"""
        return self._name

    @property
    def default_rel(self):
        return self._default_rel

    def __getattr__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        try:
            return self.get(name)
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self.get(name)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def get(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        if (
            any(x.islower() for x in name)
            and any(x.isupper() for x in name)
        ):
            given = name
            name = name[0]
            for x in given[1:]:
                if x.isupper():
                    name += "_"
                name += x
        return self._entities[name.lower()]

    def __iter__(self):
        """Iterate over the ontology entities in the namespace.

        :return: An iterator over the entities.
        :rtype: Iterator[OntologyEntity]
        """
        return iter(self._entities.values())

    def __contains__(self, obj):
        if isinstance(obj, str):
            return obj.lower() in self._entities.keys()
        return obj in self._entities.values()

    def _add_entity(self, entity):
        """Add an entity to the namespace.

        :param entity: The entity to add.
        :type entity: OntologyEntity
        """
        from osp.core.ontology.entity import OntologyEntity
        assert isinstance(entity, OntologyEntity)
        self._entities[entity.name.lower()] = entity
