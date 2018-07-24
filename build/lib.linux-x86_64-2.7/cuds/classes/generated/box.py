from cuba import CUBA
from two_dimensional_continuant_fiat_boundary import TwoDimensionalContinuantFiatBoundary


class Box(TwoDimensionalContinuantFiatBoundary):
    """
    A simple hexahedron simulation box
    """

    cuba_key = CUBA.BOX

    def __init__(self, name=None):
        super(Box, self).__init__(name)
