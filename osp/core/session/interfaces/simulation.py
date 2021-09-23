"""Interface for simulation engines."""

from abc import abstractmethod

from osp.core.session.interfaces.interface import Interface


class SimulationEngineInterface(Interface):
    """Interface for simulation engines."""

    @abstractmethod
    def run(self) -> None:
        """Ask run the simulation and wait for it to complete."""
        pass
