from cuba import CUBA
from continuant_fiat_boundary import ContinuantFiatBoundary


class ZeroDimensionalContinuantFiatBoundary(ContinuantFiatBoundary):
    """
    bfo
    """

    cuba_key = CUBA.ZERO_DIMENSIONAL_CONTINUANT_FIAT_BOUNDARY

    def __init__(self, name=None):
        super(ZeroDimensionalContinuantFiatBoundary, self).__init__(name)
