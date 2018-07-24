from cuba import CUBA
from time_unit import TimeUnit


class Second(TimeUnit):
    """
    the meter (symbol, m), used to measure distance as ...
    """

    cuba_key = CUBA.SECOND

    def __init__(self, name=None):
        super(Second, self).__init__(name)
