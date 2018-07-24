from cuba import CUBA
from physical_quality import PhysicalQuality


class Elasticity(PhysicalQuality):
    """
    To Be Determined
    """

    cuba_key = CUBA.ELASTICITY

    def __init__(self, value, name=None):
        super(Elasticity, self).__init__(value, name)
