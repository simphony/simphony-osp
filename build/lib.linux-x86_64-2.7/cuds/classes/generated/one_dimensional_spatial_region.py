from cuba import CUBA
from spatial_region import SpatialRegion


class OneDimensionalSpatialRegion(SpatialRegion):
    """
    bfo
    """

    cuba_key = CUBA.ONE_DIMENSIONAL_SPATIAL_REGION

    def __init__(self, name=None):
        super(OneDimensionalSpatialRegion, self).__init__(name)
