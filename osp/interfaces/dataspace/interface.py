"""The data space store connects OSP-core to a data space."""

from osp.core.session.interfaces.remote.client import RemoteStoreClient
from osp.core.session.interfaces.interface import Interface

from typing import Optional, Dict, Any


class DataspaceStore(RemoteStoreClient):
    """The data space store connects OSP-core to a data space."""

    def __init__(
        self,
        interface: 'DataspaceInterface',
    ):
        """Construct a data space store.

        Args:
            interface: A data space interface,
                which has received kwargs from the user.
        """
        super().__init__(
            uri=interface.uri,
            file_destination=interface.file_destination,
            connect_kwargs=interface.connect_kwargs,
            configuration_string=interface.configuration_string
        )


class DataspaceInterface(Interface):
    """The data space interface connects OSP-core to a data space."""

    store_class = DataspaceStore

    def __init__(self,
                 uri: str = '',
                 configuration_string: str = '',
                 file_destination: Optional[str] = None,
                 connect_kwargs: Optional[Dict[str, Any]] = None,
                 *args, **kwargs):
        """Intialize the interface."""
        self.configuration_string = configuration_string
        self.uri = uri
        self.file_destination = file_destination
        self.connect_kwargs = connect_kwargs
        super().__init__(*args, **kwargs)
