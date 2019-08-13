# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod
from copy import deepcopy
from cuds.classes.core.registry import Registry


class Session(ABC):
    """
    Abstract Base Class for all Sessions.
    Defines the common standard API and sets the registry.
    """
    def __init__(self):
        self._registry = Registry()
        self.root = None

    @abstractmethod
    def __str__(self):
        pass

    def store(self, entity):
        """Store a copy of given entity in the session.
        Return the stored object.

        :param entity: The entity to store.
        :type entity: Cuds
        :return: The stored entity.
        :rtype: Cuds
        """
        assert entity.session == self
        self._registry.put(entity)
        if self.root is None:
            self.root = entity.uid
        return entity

    def load(self, *uids):
        """Load the cuds objects of the given uids.

        :param uids: The uids of the cuds objects to load.
        :type uids: UUID
        :return: The fetched Cuds objects.
        :rtype: Iterator[Cuds]
        """
        for uid in uids:
            try:
                yield self._registry.get(uid)
            except KeyError:
                yield None

    def prune(self, rel=None):
        """Remove all elements not reachable from the sessions root.
        Only consider given relationship and its subclasses.

        :param rel: Only consider this relationship to calculate reachability.
        :type rel: Relationship
        """
        deleted = self._registry.prune([self.root], rel)
        for d in deleted:
            self._notify_delete(d)

    @abstractmethod
    def _notify_delete(self, entity):
        """This method is called if some object from the registry is deleted
        by the prune() method.

        :param cuds: The entity that has been deleted
        :type cuds: Cuds
        """
        pass

    @abstractmethod
    def _notify_update(self, entity):
        """This method is called if some object has been updated-

        :param entity: The entity that has been updated.
        :type entity: Cuds
        """
        pass

    def sync(self):
        pass
