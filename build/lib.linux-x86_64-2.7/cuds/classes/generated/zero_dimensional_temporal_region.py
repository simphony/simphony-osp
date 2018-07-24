from cuba import CUBA
from temporal_region import TemporalRegion


class ZeroDimensionalTemporalRegion(TemporalRegion):
    """
    bfo
    """

    cuba_key = CUBA.ZERO_DIMENSIONAL_TEMPORAL_REGION

    def __init__(self, name=None):
        super(ZeroDimensionalTemporalRegion, self).__init__(name)
