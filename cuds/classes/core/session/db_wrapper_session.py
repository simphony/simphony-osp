# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from .wrapper_session import WrapperSession


class DbWrapperSession(WrapperSession):

    def __str__(self):
        return ""

    def commit(self):
        self._engine.commit()