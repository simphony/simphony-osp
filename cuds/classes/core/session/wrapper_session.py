# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from .session import Session


class WrapperSession(Session):
    """
    Common class for all wrapper sessions.
    Sets the engine and creates the sets with the changed elements
    """
    def __init__(self, engine):
        super().__init__()
        self._engine = engine
        self._reset_buffers()

    @abstractmethod
    def __str__(self):
        pass

    # OVERRIDE
    def store(self, entity):
        """Store the entity in the registry and add it to buffers.

        :param entity: The entity to store.
        :type entity: Cuds
        """
        super().store(entity)
        if entity.uid in self._deleted:
            del self._deleted[entity.uid]

        if entity.uid in self._uid_set:
            self._updated[entity.uid] = entity
        else:
            self._added[entity.uid] = entity

    # OVERRIDE
    def _notify_update(self, entity):
        """Add the updated entity to the buffers.

        :param entity: The entity that has been updated.
        :type entity: Cuds
        :raises RuntimeError: The updated object has been deleted previously.
        """
        if entity.uid in self._deleted:
            raise RuntimeError("Cannot update deleted object")

        if entity.uid in self._uid_set:
            self._updated[entity.uid] = entity
        else:
            self._added[entity.uid] = entity

    # OVERRIDE
    def _notify_delete(self, entity):
        """Add the deleted entity to the buffers.

        :param entity: The entity that has been deleted.
        :type entity: Cuds
        """
        if entity.uid in self._added:
            del self._added[entity.uid]
        elif entity.uid in self._updated:
            del self._updated[entity.uid]
            self._deleted[entity.uid] = entity
        else:
            self._deleted[entity.uid] = entity

    def _reset_buffers(self):
        """Reset the buffers"""
        self._added = dict()
        self._updated = dict()
        self._deleted = dict()
        self._uid_set = set(self._registry.keys())

    def _check_cuds(self):
        """Check if there are any inconsistencies in the
        added or modified cuds."""
        pass

    @abstractmethod
    def _apply_added(self):
        """Add the added cuds to the engine"""
        pass

    @abstractmethod
    def _apply_updated(self):
        """Update the updated cuds in the engine"""
        pass

    @abstractmethod
    def _apply_deleted(self):
        """Delete the deleted cuds from the engine"""
        pass
