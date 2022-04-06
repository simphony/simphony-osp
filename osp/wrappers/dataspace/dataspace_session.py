"""Connect osp-core to a dataspace.

A Dataspace is like a Database backend with added functionalities.
"""

from osp.core.session import DbWrapperSession, TransportSessionClient


class DataspaceSession(TransportSessionClient):
    """The dataspace wrapper connects OSP-core to a dataspace."""

    def __init__(
        self, uri, file_destination=None, connect_kwargs=None, **kwargs
    ):
        """Construct the dataspace session.

        Args:
            uri (str): WebSocket URI.
            file_destination (str, optional): Location to store the
                downloaded files. Defaults to None.
            connect_kwargs (dict[str, Any]): Will be passed to
                websockets.connect. E.g. it is possible to pass an SSL context
                with the ssl keyword.
            kwargs (dict[str, Any]): Will be passed to the creation of the
                session object.
        """
        super().__init__(
            DbWrapperSession,
            uri,
            file_destination,
            connect_kwargs=connect_kwargs,
            **kwargs
        )
