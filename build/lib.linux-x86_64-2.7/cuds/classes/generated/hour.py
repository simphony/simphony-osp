from cuba import CUBA
from time_unit import TimeUnit


class Hour(TimeUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.HOUR

    def __init__(self, name=None):
        super(Hour, self).__init__(name)
