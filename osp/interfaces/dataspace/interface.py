"""The data space store connects OSP-core to a data space."""

from typing import Optional, Dict, Any

from rdflib import Graph
from rdflib.term import Identifier

from osp.core.interfaces.remote.client import RemoteStoreClient
from osp.core.interfaces.interface import Interface


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

    # Interface
    # ↓ ----- ↓

    base: Optional[Graph] = None

    disable_entity_tracking: bool = True

    root: Optional[Identifier] = None

    def open(self, configuration: str, create: bool = False):
        """Open the specified dataspace."""
        if self.base is not None:
            raise RuntimeError('The remote store is already open!')

        dataspace_store = DataspaceStore(interface=self)
        self.base = Graph(store=dataspace_store)
        self.base.open(configuration, create)

    def close(self):
        """Close the dataspace."""
        if self.base is not None:
            self.base.close(commit_pending_transaction=False)
            self.base = None

    def commit(self):
        """Commit pending changes to the triple store."""
        # The `InterfaceDriver` will simply add the triples to the base graph
        # and commit them. Nothing to do here.
        pass

    def populate(self):
        """The base graph does not need to be populated. Nothing to do."""
        pass

    # ↑ ----- ↑

    def __init__(self,
                 uri: str = '',
                 configuration_string: str = '',
                 file_destination: Optional[str] = None,
                 connect_kwargs: Optional[Dict[str, Any]] = None,
                 *args, **kwargs):
        """Initialize the interface."""
        self.configuration_string = configuration_string
        self.uri = uri
        self.file_destination = file_destination
        self.connect_kwargs = connect_kwargs
        super().__init__(*args, **kwargs)
