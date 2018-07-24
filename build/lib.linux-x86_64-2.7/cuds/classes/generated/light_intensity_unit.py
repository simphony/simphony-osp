from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class LightIntensityUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of ...
    """

    cuba_key = CUBA.LIGHT_INTENSITY_UNIT

    def __init__(self, name=None):
        super(LightIntensityUnit, self).__init__(name)
