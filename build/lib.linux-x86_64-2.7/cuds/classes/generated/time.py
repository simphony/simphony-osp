from cuba import CUBA
from physical_quality import PhysicalQuality


class Time(PhysicalQuality):
    """
    A time quality, in units with origin t=0
    """

    cuba_key = CUBA.TIME

    def __init__(self, value, name=None):
        super(Time, self).__init__(value, name)
