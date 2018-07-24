from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class LengthUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of the distance between two points.
    Used to designate unit system universals
    """

    cuba_key = CUBA.LENGTH_UNIT

    def __init__(self, name=None):
        super(LengthUnit, self).__init__(name)
