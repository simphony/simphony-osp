from cuba import CUBA
from length_unit import LengthUnit


class Centimeter(LengthUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.CENTIMETER

    def __init__(self, name=None):
        super(Centimeter, self).__init__(name)
