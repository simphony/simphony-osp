from cuba import CUBA
from cuds import Cuds


class PhysicalSystem(Cuds):
    """
    (CWA) collection of entities used to represent a (whole) material. A
    representation of the physics state in terms of the entities and their
    properties (quantitis)
    """

    cuba_key = CUBA.PHYSICAL_SYSTEM

    def __init__(self, name=None):
        super(PhysicalSystem, self).__init__(name)
