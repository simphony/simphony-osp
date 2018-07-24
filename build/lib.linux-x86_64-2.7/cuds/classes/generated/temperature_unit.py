from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class TemperatureUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of ...
    """

    cuba_key = CUBA.TEMPERATURE_UNIT

    def __init__(self, name=None):
        super(TemperatureUnit, self).__init__(name)
