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
from cuds.classes.core.session.wrapper_session import consumes_buffers
from cuds.classes.core.session.storage_wrapper_session import \
    StorageWrapperSession


class DbWrapperSession(StorageWrapperSession):

    @consumes_buffers
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

    def load_by_cuba_key(self, cuba_key, update_registry=False):
        """Load cuds all cuds with given cuba key.
        Will not replace cuds in registry.

        :param cuba_key: The cuby key to query for
        :type cuba_key: CUBA
        :param update_registry: Whether to update cuds objects already
            present in the registry.
        :type update_registry: bool
        :return: The list of loaded cuds
        :rtype: Iterator[Cuds]
        """
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")
        yield from self._load_by_cuba(cuba_key, update_registry=False)

    def store(self, entity):
        initialize = self.root is None
        super().store(entity)

        if initialize:
            self._initialize()
            self._load_first_level()
            self._reset_buffers(changed_by="engine")

    def _commit(self):
        """Commit to the database"""
        self._engine.commit()

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

    @abstractmethod
    def _load_by_cuba(self, uids, update_registry=False):
        """Load the Cuds entity with the given cuba.
        If uid is None return all entities with given cuba_key.

        :param cuba: The Cuba-Key of the cuds object
        :type cuba: CUBA
        :param update_registry: Whether to update cuds objects already
            present in the registry.
        :type update_registry: bool
        :return: The loaded Cuds entity.
        :rtype: Cuds
        """
        pass
