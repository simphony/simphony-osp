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
