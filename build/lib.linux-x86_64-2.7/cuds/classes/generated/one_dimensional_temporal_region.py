from cuba import CUBA
from temporal_region import TemporalRegion


class OneDimensionalTemporalRegion(TemporalRegion):
    """
    bfo
    """

    cuba_key = CUBA.ONE_DIMENSIONAL_TEMPORAL_REGION

    def __init__(self, name=None):
        super(OneDimensionalTemporalRegion, self).__init__(name)
