# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod
from ..registry import Registry


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

    def add(self, entity):
        self._registry.put(entity)
        if self.root is None:
            self.root = entity.uid

    def load(self):
        pass

    def sync(self):
        pass
