# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from .wrapper_session import WrapperSession, consumes_buffers


class SimWrapperSession(WrapperSession):
    def __init__(self, engine, **kwargs):
        super().__init__(engine, **kwargs)
        self._ran = False

    @consumes_buffers
    def run(self):
        self._check_cardinalities()
        root_cuds = self._registry.get(self.root)
        self._apply_added()
        self._apply_updated()
        self._apply_deleted()
        self._reset_buffers(changed_by="user")
        self._run(root_cuds)
        self._update_cuds_objects_after_run(root_cuds)
        self._reset_buffers(changed_by="engine")
        self._ran = True

    @abstractmethod
    def _run(self, root_cuds_object):
        """Call the run command of the engine. """

    @abstractmethod
    def _update_cuds_objects_after_run(self, root_cuds_object):
        """Update the cuds_object after the engine has been executed. """

    @abstractmethod
    def _apply_added(self):
        """Add the added cuds_objects to the engine"""

    @abstractmethod
    def _apply_updated(self):
        """Update the updated cuds_objects in the engine"""

    @abstractmethod
    def _apply_deleted(self):
        """Delete the deleted cuds_objects from the engine"""
