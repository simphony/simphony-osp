# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from .wrapper_session import WrapperSession


class DbWrapperSession(WrapperSession):
    def __init__(self, engine):
        super().__init__(engine)
        self._initialize_tables()
        self._load_first_level()

    def __str__(self):
        return ""

    def commit(self):
        self._apply_added()
        self._apply_updated()
        self._apply_deleted()
        self._engine.commit()
        self._reset_buffers()

    def close(self):
        self._engine.close()

    # OVERRIDE
    def load(self, *uids):
        """Look in the DB if element not in the registry.

        :param uids: The uids of the cuds objects to load.
        :type uids: UUID
        :return: The fetched Cuds objects.
        :rtype: Iterator[Cuds]
        """
        missing_uids = [uid for uid in uids if uid not in self._registry]
        missing = self._load_missing(*missing_uids)
        for uid in uids:
            if uid in self._registry:
                yield self._registry.get(uid)
            else:
                entity = next(missing)
                if entity is not None:
                    self._uid_set.add(entity.uid)
                yield entity

    @abstractmethod
    def _initialize_tables(self):
        """Create master tables if they don't exit"""
        pass

    @abstractmethod
    def _load_first_level(self):
        """Load the first level of entities
        """
        pass

    def _apply_added(self):
        """Perform the SQL-Statements to add the elements
        in the buffers to the DB."""
        pass

    @abstractmethod
    def _apply_updated(self):
        """Perform the SQL-Statements to update the elements
        in the buffers in the DB."""
        pass

    @abstractmethod
    def _apply_deleted(self):
        """Perform the SQL-Statements to delete the elements
        in the buffers in the DB."""
        pass

    @abstractmethod
    def _load_missing(self, *uids):
        """Load the missing entities from the database.

        : param uids: The uids od the entities to load.
        : type uids: UUID
        : return: The loaded entities.
        : rtype: Iterator[Cuds]
        """
        pass
