from cuba import CUBA
from physical_quality import PhysicalQuality


class Color(PhysicalQuality):
    """
    To Be Determined
    """

    cuba_key = CUBA.COLOR

    def __init__(self, value, name=None):
        super(Color, self).__init__(value, name)
