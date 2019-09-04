# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from sqlalchemy import create_engine
from abc import abstractmethod
from cuds.classes.core.session.wrapper_session import WrapperSession


class DbWrapperSession(WrapperSession):

    def commit(self):
        """Commit the changes in the buffers to the database."""
        self._check_cardinalities()
        self._apply_added()
        self._apply_updated()
        self._apply_deleted()
        self._reset_buffers(changed_by="user")
        self._commit()
        self._reset_buffers(changed_by="engine")

    def load_by_cuba_key(self, cuba_key):
        """Load cuds all cuds with given cuba key.
        Will not replace cuds in registry.

        :param cuba_key: The cuby key to query for
        :type cuba_key: CUBA
        :return: The list of loaded cuds
        :rtype: Iterator[Cuds]
        """
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")
        entities = self._load_cuds(uids=None, cuba_key=cuba_key)
        for i, entity in enumerate(entities):
            if entity.uid in self._registry:
                entities[i] = self._registry.get(entity.uid)
        return entities

    def store(self, entity):
        initialize = self.root is None
        super().store(entity)

        if initialize:
            self._initialize()
            self._load_first_level()
            self._reset_buffers(changed_by="engine")

    # OVERRIDE
    def load(self, *uids):
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")

        missing_uids = [uid for uid in uids if uid not in self._registry]
        # Load elements not in the registry from the database
        missing = self._load_cuds(missing_uids)
        for uid in uids:
            if uid in self._registry:
                yield self._registry.get(uid)
            else:
                entity = next(missing)
                if entity is not None:
                    self._uid_set.add(entity.uid)
                    del self._added[entity.uid]
                yield entity

    def _commit(self):
        """Commit to the database"""
        self._engine.commit()

    @abstractmethod
    def _load_cuds(self, uids, cuba_key=None):
        """Load cuds with given uids or cuba_key from the database

        :param uids: List of uids to load
        :type uids: List[uuid.UUID]
        :param cuba_key: Load all entities with this cuba_key, defaults to None
        :type cuba_key: CUBA, optional
        """
        pass

    @abstractmethod
    def _initialize(self):
        """Initialize the database. Create missing tables etc."""
        pass

    @abstractmethod
    def _load_first_level(self):
        """Load the first level of children of the root from the database."""
        pass

    @abstractmethod
    def close(self):
        """Close the connection to the database"""
        pass
