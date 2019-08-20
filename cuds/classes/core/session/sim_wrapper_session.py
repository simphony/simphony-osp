# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from .wrapper_session import WrapperSession


class SimWrapperSession(WrapperSession):
    def __init__(self, engine):
        super().__init__(engine)
        self._ran = False

    def run(self):
        self._check_cuds()
        self._apply_added()
        self._apply_updated()
        self._apply_deleted()
        self._run()
        self._update_cuds_after_run()
        self._reset_buffers()

    @abstractmethod
    def _run(self):
        """Call the run command of the engine. """
        pass

    @abstractmethod
    def _update_cuds_after_run(self):
        """Update the cuds after the engine has been executed. """
        pass
