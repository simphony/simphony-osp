# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
from abc import abstractmethod
from cuds.utils import destroy_cuds_object
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

        # Load elements not in the registry / expired from the backend
        missing = self._load_from_backend(missing_uids, expired=expired)
        for uid in uids:

            # Load from registry if uid is there and not expired
            if uid not in missing_uids:
                yield self._registry.get(uid)
                continue

            # Load from backend if not in registry or expired
            try:
                cuds_object = next(missing)
            except StopIteration:
                cuds_object = None  # not available in the backend

            # avoid changes in the buffers
            if cuds_object is not None:
                self._remove_uids_from_buffers([uid])

            # expired object no longer present in the backend --> delete it
            elif uid in self._registry:
                self._remove_uids_from_buffers([uid])
                self._uids_in_registry_after_last_buffer_reset -= {uid}
                old = self._registry.get(uid)
                destroy_cuds_object(old)
            yield cuds_object

    def expire(self, *cuds_or_uids):
        """Let cuds_objects expire. Expired objects will be reloaded lazily
        when attributed or relationships are accessed.

        :param cuds_or_uids: The cuds_object or uids to expire
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
        """Let all cuds_objects of the session expire.
        Expired objects will be reloaded lazily
        when attributed or relationships are accessed.
        """
        self._expired = set(self._registry.keys()) - set([self.root])

    def refresh(self, *cuds_or_uids):
        """Refresh cuds_objects. Load possibly data of cuds_object
        from the backend.  # TODO expire old/new neighbors?

        :param *cuds_or_uids: The cuds_object or uids to refresh
        :type *cuds_or_uids: Union[Cuds, UUID]
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
        self._expired |= uids
        list(self.load(*uids))

    # OVERRIDE
    def _notify_read(self, cuds_object):
        if cuds_object.uid in self._expired:
            self.refresh(cuds_object)

    @abstractmethod
    def _load_from_backend(self, uids, expired=None):
        """Load cuds_object with given uids from the database.
        Will update objects with same uid in the registry.

        :param uids: List of uids to load
        :type uids: List[UUID]
        :param expired: Which of the cuds_objects are expired.
        :type expired: Set[UUID]
        """
        pass
