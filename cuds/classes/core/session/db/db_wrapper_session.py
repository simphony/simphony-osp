# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
from sqlalchemy import create_engine
from abc import abstractmethod
from cuds.utils import destruct_cuds
from cuds.classes.core.session.wrapper_session import WrapperSession


class DbWrapperSession(WrapperSession):

    def __init__(self, engine, **kwargs):
        super().__init__(engine, **kwargs)
        self._expired = set()

    def commit(self):
        """Commit the changes in the buffers to the database."""
        self._check_cardinalities()
        self._init_transaction()
        try:
            self._apply_added()
            self._apply_updated()
            self._apply_deleted()
            self._reset_buffers(changed_by="user")
            self._commit()
        except Exception as e:
            self._rollback_transaction()
            raise e
        self._reset_buffers(changed_by="engine")
        self.expire_all()

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
        yield from self._load_cuds(uids=None, cuba_key=cuba_key,
                                   update_registry=False)

    def expire(self, *cuds_or_uids):
        for c in cuds_or_uids:
            if isinstance(c, uuid.UUID):
                assert c != self.root, "Cannot expire root"
                self._expired.add(c)
            else:
                assert c != self.root, "Cannot expire root"
                self._expired.add(c.uid)

    def expire_all(self):
        self._expired = set(self._registry.keys()) - set([self.root])

    def refresh(self, *cuds_or_uids):
        uids = list()
        for c in cuds_or_uids:
            if isinstance(c, uuid.UUID):
                uids.append(c)
            else:
                uids.append(c.uid)
        uids = set(uids) - set([self.root])
        self._expired -= uids
        loaded = list(self._load_cuds(uids, update_registry=True))
        for uid, loaded_entity in zip(uids, loaded):
            if loaded_entity is None:
                old = self._registry.get(uid)
                destruct_cuds(old)

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

        # refresh expired
        expired = set(uids) & self._expired
        self.refresh(*expired)

        missing_uids = [uid for uid in uids if uid not in self._registry]
        # Load elements not in the registry from the database
        missing = self._load_cuds(missing_uids, update_registry=False)
        for uid in uids:
            if uid in self._registry:
                yield self._registry.get(uid)
            else:
                try:
                    entity = next(missing)
                except StopIteration:
                    entity = None
                if entity is not None:
                    self._uid_set.add(entity.uid)
                    del self._added[entity.uid]
                yield entity

    # OVERRIDE
    def _notify_read(self, entity):
        if entity.uid in self._expired:
            self.refresh(entity)

    def _commit(self):
        """Commit to the database"""
        self._engine.commit()

    @abstractmethod
    def _load_cuds(self, uids, cuba_key=None, update_registry=False):
        """Load cuds with given uids or cuba_key from the database

        :param uids: List of uids to load
        :type uids: List[uuid.UUID]
        :param cuba_key: Load all entities with this cuba_key, defaults to None
        :type cuba_key: CUBA, optional
        :param update_registry: Whether to override the cuds in the registry
        :type update_registry: bool
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
    def _init_transaction(self):
        """Initialize the transaction"""
        pass

    @abstractmethod
    def _rollback_transaction(self):
        """Initialize the transaction"""
        pass

    @abstractmethod
    def close(self):
        """Close the connection to the database"""
        pass
