from cuba import CUBA
from physical_quality import PhysicalQuality


class Distance(PhysicalQuality):
    """
    A quality that is the extent of space between two entities.
    """

    cuba_key = CUBA.DISTANCE

    def __init__(self, value, name=None):
        super(Distance, self).__init__(value, name)
