# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from cuds.session.wrapper_session import consumes_buffers
from cuds.session.storage_wrapper_session import \
    StorageWrapperSession


class DbWrapperSession(StorageWrapperSession):
    """Abstract class for a DB Wrapper Session"""

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
        """Load cuds_object with given cuba key.
        Will not replace cuds_object in registry.

        :param cuba_key: The cuba key to query for
        :type cuba_key: CUBA
        :param update_registry: Whether to update cuds_objects which are
            already present in the registry.
        :type update_registry: bool
        :return: The list of loaded cuds objects
        :rtype: Iterator[Cuds]
        """
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")
        yield from self._load_by_cuba(cuba_key, update_registry=False)

    def store(self, cuds_object):
        initialize = self.root is None
        super().store(cuds_object)

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

    @abstractmethod
    def _apply_added(self):
        """Add the added cuds_objects to the engine"""

    @abstractmethod
    def _apply_updated(self):
        """Update the updated cuds_objects in the engine"""

    @abstractmethod
    def _apply_deleted(self):
        """Delete the deleted cuds_objects from the engine"""

    @abstractmethod
    def _load_first_level(self):
        """Load the first level of children of the root from the database."""

    @abstractmethod
    def _init_transaction(self):
        """Initialize the transaction"""

    @abstractmethod
    def _rollback_transaction(self):
        """Initialize the transaction"""

    @abstractmethod
    def close(self):
        """Close the connection to the database"""

    @abstractmethod
    def _load_by_cuba(self, cuba, update_registry=False):
        """Load the cuds_object with the given cuba.

        :param cuba: The Cuba-Key of the cuds objects
        :type cuba: CUBA
        :param update_registry: Whether to update cuds_objects already
            which are already present in the registry.
        :type update_registry: bool
        :return: The loaded cuds_object.
        :rtype: Cuds
        """
