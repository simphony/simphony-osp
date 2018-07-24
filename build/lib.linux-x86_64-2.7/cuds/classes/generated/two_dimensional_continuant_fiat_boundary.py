from cuba import CUBA
from continuant_fiat_boundary import ContinuantFiatBoundary


class TwoDimensionalContinuantFiatBoundary(ContinuantFiatBoundary):
    """
    bfo
    """

    cuba_key = CUBA.TWO_DIMENSIONAL_CONTINUANT_FIAT_BOUNDARY

    def __init__(self, name=None):
        super(TwoDimensionalContinuantFiatBoundary, self).__init__(name)
