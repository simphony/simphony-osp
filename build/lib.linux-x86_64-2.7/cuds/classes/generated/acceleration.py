from cuba import CUBA
from physical_quality import PhysicalQuality


class Acceleration(PhysicalQuality):
    """
    the time derivative of the velocity of an entity
    """

    cuba_key = CUBA.ACCELERATION

    def __init__(self, value, name=None):
        super(Acceleration, self).__init__(value, name)
