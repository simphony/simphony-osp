"""Interface between the SimPhoNy OSP and SQLAlchemy."""

from typing import Dict, Optional

from rdflib import Graph, URIRef
from rdflib.term import Identifier

from simphony_osp.interfaces.interface import BufferType, Interface


class SQLAlchemy(Interface):
    """An interface to an SQL database using SQLAlchemy."""

    _identifier: Identifier = URIRef("https://www.simphony-osp.eu/SQLAlchemy")
    """The identifier of the graph serving as context of the saved triples."""

    _uri: Optional[str] = None
    """SQLAlchemy URI used to connect to the database."""

    _buffers: Optional[Dict[BufferType, Graph]]
    """Triple buffers (see docstring of `BufferType`)."""

    base: Optional[Graph] = None
    """Representation of the contents of the database as an RDFLib graph
    using the `rdflib-sqlalchemy` plug-in."""

    # Interface
    # ↓ ----- ↓

    entity_tracking: bool = False

    def open(self, configuration: str, create: bool = False):
        """Open a connection to the database.

        Args:
            configuration: The SQLAlchemy URI pointing to the database to
                which the user wishes to connect.
            create: Whether to create the database file if it does not exist.
        """
        # TODO: Create databases if create is `True`.
        if self._uri is not None and self._uri != configuration:
            raise RuntimeError(
                f"A different database {self._uri}" f"is already open!"
            )

        self.base = Graph("SQLAlchemy", identifier=self._identifier)
        self.base.open(configuration, create=create)
        self._uri = configuration

    def close(self) -> None:
        """Close the connection to the database."""
        if self.base is not None:
            self.base.close(commit_pending_transaction=False)
            self._uri = None
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
