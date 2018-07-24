from cuba import CUBA
from length_unit import LengthUnit


class Meter(LengthUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.METER

    def __init__(self, name=None):
        super(Meter, self).__init__(name)
