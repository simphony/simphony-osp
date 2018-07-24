from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class TimeUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of ...
    """

    cuba_key = CUBA.TIME_UNIT

    def __init__(self, name=None):
        super(TimeUnit, self).__init__(name)
