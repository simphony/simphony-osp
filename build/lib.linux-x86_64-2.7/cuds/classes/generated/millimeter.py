from cuba import CUBA
from length_unit import LengthUnit


class Millimeter(LengthUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.MILLIMETER

    def __init__(self, name=None):
        super(Millimeter, self).__init__(name)
