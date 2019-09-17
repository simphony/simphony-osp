# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
from abc import abstractmethod
from cuds.utils import destruct_cuds
from cuds.classes.core.session.wrapper_session import WrapperSession


class StorageWrapperSession(WrapperSession):

    def __init__(self, engine, **kwargs):
        super().__init__(engine, **kwargs)
        self._expired = set()

    # OVERRIDE
    def load(self, *uids):
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")

        # refresh expired
        expired = frozenset(set(uids) & self._expired)
        missing_uids = [uid for uid in uids
                        if uid not in self._registry or uid in expired]
        self._expired -= expired
        # Load elements not in the registry from the database
        missing = self._load_cuds(missing_uids)
        for uid in uids:
            if uid not in missing_uids:
                yield self._registry.get(uid)
            else:
                try:
                    entity = next(missing)
                except StopIteration:
                    entity = None
                if entity is not None:
                    self._uid_set.add(entity.uid)
                    if entity.uid in self._added:
                        del self._added[entity.uid]
                yield entity

    def expire(self, *cuds_or_uids):
        """Let cuds objects expire. Expired objects will be reloaded lazily
        when attributed or relationships are accessed.

        :param cuds_or_uids: The cuds or uids to expire
        :type cuds_or_uids: Union[Cuds, UUID]
        """
        for c in cuds_or_uids:
            if isinstance(c, uuid.UUID):
                assert c != self.root, "Cannot expire root"
                self._expired.add(c)
            else:
                assert c != self.root, "Cannot expire root"
                self._expired.add(c.uid)
        self._expired &= (set(self._registry.keys()) - set([self.root]))

    def expire_all(self):
        """Let all cuds objects of the session expire.
        Expired objects will be reloaded lazily
        when attributed or relationships are accessed.
        """
        self._expired = set(self._registry.keys()) - set([self.root])

    def refresh(self, *cuds_or_uids):
        """Refresh a cuds objects. Load possibly data of cuds object
        from the backend.

        :param cuds_or_uids: The cuds or uids to expire
        :type cuds_or_uids: Union[Cuds, UUID]
        """
        if not cuds_or_uids:
            return
        uids = list()
        for c in cuds_or_uids:
            if isinstance(c, uuid.UUID):
                uids.append(c)
            else:
                uids.append(c.uid)
        uids = set(uids) - set([self.root])
        old_expired = frozenset(self._expired)
        self._expired -= uids
        loaded = list(self._load_cuds(uids, old_expired))
        for uid, loaded_entity in zip(uids, loaded):
            if loaded_entity is None:
                old = self._registry.get(uid)
                destruct_cuds(old)

    # OVERRIDE
    def _notify_read(self, entity):
        if entity.uid in self._expired:
            self.refresh(entity)

    @abstractmethod
    def _load_cuds(self, uids, expired=None):
        """Load cuds with given uids from the database.
        Will update objects with same uid in the registry.

        :param uids: List of uids to load
        :type uids: List[UUID]
        :param expired: Which of the cuds objects are expired-
            Usually this is not used.
        :type expired: Set[UUID]
        """
        pass
