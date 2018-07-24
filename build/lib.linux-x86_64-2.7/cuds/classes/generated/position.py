from cuba import CUBA
from physical_quality import PhysicalQuality


class Position(PhysicalQuality):
    """
    position of an entity
    """

    cuba_key = CUBA.POSITION

    def __init__(self, value, name=None):
        super(Position, self).__init__(value, name)
