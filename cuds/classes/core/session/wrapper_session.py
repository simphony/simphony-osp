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
    @abstractmethod
    def __str__(self):
        pass

    def __init__(self, engine):
        super().__init__()
        self._engine = engine
        self._added = set()
        self._updated = set()
        self._removed = set()

    def add(self, entity):
        super().add(entity)
        self._added.add(entity)
