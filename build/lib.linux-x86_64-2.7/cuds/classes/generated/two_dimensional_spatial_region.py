from cuba import CUBA
from spatial_region import SpatialRegion


class TwoDimensionalSpatialRegion(SpatialRegion):
    """
    bfo
    """

    cuba_key = CUBA.TWO_DIMENSIONAL_SPATIAL_REGION

    def __init__(self, name=None):
        super(TwoDimensionalSpatialRegion, self).__init__(name)
