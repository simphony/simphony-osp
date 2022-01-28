"""Interface for simulation engines."""

from abc import ABC

from rdflib import Graph

from osp.core.interfaces.overlay import OverlayDriver, OverlayInterface
from osp.core.session import Session


class SimulationDriver(OverlayDriver):
    """RDFLib store with the added capability of running a simulation."""

    interface: 'SimulationInterface'

    # RDFLib
    # ↓ -- ↓

    context_aware = False
    formula_aware = False
    transaction_aware = True
    graph_aware = False

    def __init__(self, *args, **kwargs):
        """Initialize the SimulationDriver."""
        super().__init__(*args, **kwargs)

    def open(self, *args, **kwargs):
        """Asks the interface to open the data source."""
        return super().open(*args, **kwargs)

    def close(self, *args, **kwargs):
        """Tells the interface to close the data source."""
        return super().close(*args, **kwargs)

    def add(self, *args, **kwargs):
        """Adds triples to the store."""
        return super().add(*args, **kwargs)

    def remove(self, *args, **kwargs):
        """Remove triples from the store."""
        return super().remove(*args, **kwargs)

    def triples(self, *args, **kwargs):
        """Query triples patterns."""
        return super().triples(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        """Get the number of triples in the store."""
        return super().__len__(*args, **kwargs)

    def bind(self, *args, **kwargs):
        """Bind a namespace to a prefix."""
        return super().bind(*args, **kwargs)

    def namespace(self, *args, **kwargs):
        """Bind a namespace to a prefix."""
        return super().namespace(*args, **kwargs)

    def prefix(self, *args, **kwargs):
        """Get a bound namespace's prefix."""
        return super().prefix(*args, **kwargs)

    def namespaces(self):
        """Get the bound namespaces."""
        return super().namespaces()

    def query(self, *args, **kwargs):
        """Perform a SPARQL query on the store."""
        return super().query(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Perform a SPARQL update query on the store."""
        return super().update(*args, **kwargs)

    def commit(self):
        """Commit buffered changes."""
        return super().commit()

    def rollback(self):
        """Discard uncommitted changes."""
        return super().rollback()

    # RDFLib
    # ↑ -- ↑

    def run(self):
        """Instructs the simulation engine interface to run the simulation."""
        try:
            self.interface.session.lock()
            with self.interface.session as session:
                self.interface.run(self.interface.graph,
                                   self.interface.session)
        finally:
            self.interface.session.unlock()


class SimulationInterface(ABC, OverlayInterface):
    """Interface for simulation engines."""

    # Definition of:
    # SimulationEngineInterface
    # ↓ --------------------- ↓

    def run(self, graph: Graph, session: Session) -> None:
        """Run the simulation and wait for it to complete.

        After it is finished, you have to update the ontology representation of
        the contents of the simulation. In order to do so, you will have to
        check what is changed and change the representation either in its
        graph form or using the session (ontological form). You can create
        new entities if you wish.
        """
        pass

    # + Methods and properties from definition of: OverlayInterface.

    # ↑ --------------------- ↑
    # Definition of:
    # SimulationEngineInterface

    driver = SimulationDriver
