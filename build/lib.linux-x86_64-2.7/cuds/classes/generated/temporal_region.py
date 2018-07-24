from cuba import CUBA
from occurrent import Occurrent


class TemporalRegion(Occurrent):
    """
    bfo
    """

    cuba_key = CUBA.TEMPORAL_REGION

    def __init__(self, name=None):
        super(TemporalRegion, self).__init__(name)
