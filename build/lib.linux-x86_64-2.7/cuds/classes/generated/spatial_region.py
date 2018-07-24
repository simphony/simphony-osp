from cuba import CUBA
from immaterial_entity import ImmaterialEntity


class SpatialRegion(ImmaterialEntity):
    """
    bfo
    """

    cuba_key = CUBA.SPATIAL_REGION

    def __init__(self, name=None):
        super(SpatialRegion, self).__init__(name)
