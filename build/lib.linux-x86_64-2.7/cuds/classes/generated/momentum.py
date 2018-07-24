from cuba import CUBA
from physical_quality import PhysicalQuality


class Momentum(PhysicalQuality):
    """
    the kinetic momentum of an entity
    """

    cuba_key = CUBA.MOMENTUM

    def __init__(self, value, name=None):
        super(Momentum, self).__init__(value, name)
