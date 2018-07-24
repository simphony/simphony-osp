from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class MassUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of the mass
    """

    cuba_key = CUBA.MASS_UNIT

    def __init__(self, name=None):
        super(MassUnit, self).__init__(name)
