class SimulationEngineInterface(Interface):

    @abstractmethod
    def run(self) -> None:
        pass
