from cuba import CUBA
from cuds import Cuds


class Simulation(Cuds):
    """
    CWA, all components of the simulation that are needed to run the model
    """

    cuba_key = CUBA.SIMULATION

    def __init__(self, name=None):
        super(Simulation, self).__init__(name)
