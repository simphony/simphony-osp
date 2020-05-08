# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.session import TransportSessionClient
from osp.core.session import DbWrapperSession


class DataspaceSession(TransportSessionClient):
    """The dataspace wrapper connects OSP-core to a dataspace."""

    def __init__(self, uri, file_destination=None):
        """Constructs the dataspace session.

        Args:
            uri (str): WebSocket URI.
            file_destination(str): Location to store the downloaded files.
        """
        super().__init__(DbWrapperSession, uri, file_destination)
