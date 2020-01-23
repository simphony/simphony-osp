# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from .wrapper_session import WrapperSession, consumes_buffers
from osp.core.session.buffers import BufferContext


class SimWrapperSession(WrapperSession):
    def __init__(self, engine, **kwargs):
        super().__init__(engine, **kwargs)
        self._ran = False

    @consumes_buffers
    def run(self):
        self.log_buffer_status(BufferContext.USER)
        self._check_cardinalities()
        root_obj = self._registry.get(self.root)
        added, updated, deleted = self._buffers[BufferContext.USER]
        self._apply_added(root_obj, added)
        self._apply_updated(root_obj, updated)
        self._apply_deleted(root_obj, deleted)
        self._reset_buffers(BufferContext.USER)
        self._run(root_obj)
        self._ran = True
        self.expire_all()

    @abstractmethod
    def _run(self, root_cuds_object):
        """Call the run command of the engine. """

    @abstractmethod
    def _apply_added(self, root_obj, buffer):
        """Add the added cuds_objects to the engine"""

    @abstractmethod
    def _apply_updated(self, root_obj, buffer):
        """Update the updated cuds_objects in the engine"""

    @abstractmethod
    def _apply_deleted(self, root_obj, buffer):
        """Delete the deleted cuds_objects from the engine"""
