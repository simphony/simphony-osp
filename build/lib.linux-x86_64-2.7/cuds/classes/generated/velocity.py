from cuba import CUBA
from physical_quality import PhysicalQuality


class Velocity(PhysicalQuality):
    """
    the velocity of an entity
    """

    cuba_key = CUBA.VELOCITY

    def __init__(self, value, name=None):
        super(Velocity, self).__init__(value, name)
