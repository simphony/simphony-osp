from cuba import CUBA
from physical_quality import PhysicalQuality


class StressTensor(PhysicalQuality):
    """
    a matrix wit 9 components for the tensor in ...
    """

    cuba_key = CUBA.STRESS_TENSOR

    def __init__(self, value, name=None):
        super(StressTensor, self).__init__(value, name)
