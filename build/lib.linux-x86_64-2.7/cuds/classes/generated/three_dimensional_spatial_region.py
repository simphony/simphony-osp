from cuba import CUBA
from spatial_region import SpatialRegion


class ThreeDimensionalSpatialRegion(SpatialRegion):
    """
    bfo
    """

    cuba_key = CUBA.THREE_DIMENSIONAL_SPATIAL_REGION

    def __init__(self, name=None):
        super(ThreeDimensionalSpatialRegion, self).__init__(name)
