from cuba import CUBA
from time_unit import TimeUnit


class Minute(TimeUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.MINUTE

    def __init__(self, name=None):
        super(Minute, self).__init__(name)
