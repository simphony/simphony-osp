# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


from .session import Session


class CoreSession(Session):
    """
    Core default session for all objects.
    """
    def __str__(self):
        return "<CoreSession object>"

    # OVERRIDE
    def _notify_update(self, entity):
        pass

    # OVERRIDE
    def _notify_delete(self, entity):
        pass

    # OVERRIDE
    def _notify_read(self, entity):
        pass
