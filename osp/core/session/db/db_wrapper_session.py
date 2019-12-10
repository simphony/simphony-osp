# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from osp.core.session.wrapper_session import consumes_buffers, WrapperSession
from osp.core.session.result import returns_query_result


class DbWrapperSession(WrapperSession):
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

    @returns_query_result
    def load_by_oclass(self, oclass, update_registry=False):
        """Load cuds_object with given OntologyClass.
        Will also return cuds objects of subclasses of oclass.

        :param oclass: Load cuds objects with this ontology class
        :type oclass: OntologyClass
        :param update_registry: Whether to update cuds_objects which are
            already present in the registry.
        :type update_registry: bool
        :return: The list of loaded cuds objects
        :rtype: Iterator[Cuds]
        """
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")
        for subclass in oclass.subclasses:
            yield from self._load_by_oclass(subclass,
                                            update_registry=update_registry)

    def _store(self, cuds_object):
        initialize = self.root is None
        super()._store(cuds_object)

        if initialize:
            self._init_transaction()
            try:
                self._initialize()
                self._load_first_level()
                self._reset_buffers(changed_by="engine")
                self._commit()
            except Exception as e:
                self._rollback_transaction()
                raise e

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
    def _load_by_oclass(self, oclass, update_registry=False):
        """Load the cuds_object with the given ontology class.

        :param oclass: The OntologyClass of the cuds objects
        :type oclass: OntologyClass
        :param update_registry: Whether to update cuds_objects already
            which are already present in the registry.
        :type update_registry: bool
        :return: The loaded cuds_object.
        :rtype: Cuds
        """
