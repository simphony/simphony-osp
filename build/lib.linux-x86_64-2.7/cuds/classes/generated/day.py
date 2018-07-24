from cuba import CUBA
from time_unit import TimeUnit


class Day(TimeUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.DAY

    def __init__(self, name=None):
        super(Day, self).__init__(name)
