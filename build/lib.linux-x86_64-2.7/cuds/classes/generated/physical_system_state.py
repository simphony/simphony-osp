from cuba import CUBA
from physical_system import PhysicalSystem


class PhysicalSystemState(PhysicalSystem):
    """
    is a physical system at specific time i.e., with values of the physics
    quantities for a physical system at an instant of time
    """

    cuba_key = CUBA.PHYSICAL_SYSTEM_STATE

    def __init__(self, name=None):
        super(PhysicalSystemState, self).__init__(name)
