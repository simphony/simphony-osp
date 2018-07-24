from cuba import CUBA
from two_dimensional_continuant_fiat_boundary import TwoDimensionalContinuantFiatBoundary


class ComputationalBoundary(TwoDimensionalContinuantFiatBoundary):
    """
    A computational (not real) boundary in the system
    """

    cuba_key = CUBA.COMPUTATIONAL_BOUNDARY

    def __init__(self, name=None):
        super(ComputationalBoundary, self).__init__(name)
