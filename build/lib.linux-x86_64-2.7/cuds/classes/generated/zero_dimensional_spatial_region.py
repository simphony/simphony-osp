from cuba import CUBA
from spatial_region import SpatialRegion


class ZeroDimensionalSpatialRegion(SpatialRegion):
    """
    bfo
    """

    cuba_key = CUBA.ZERO_DIMENSIONAL_SPATIAL_REGION

    def __init__(self, name=None):
        super(ZeroDimensionalSpatialRegion, self).__init__(name)
