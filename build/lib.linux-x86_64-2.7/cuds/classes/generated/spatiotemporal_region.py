from cuba import CUBA
from occurrent import Occurrent


class SpatiotemporalRegion(Occurrent):
    """
    bfo
    """

    cuba_key = CUBA.SPATIOTEMPORAL_REGION

    def __init__(self, name=None):
        super(SpatiotemporalRegion, self).__init__(name)
