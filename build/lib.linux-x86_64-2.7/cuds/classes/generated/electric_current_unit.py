from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class ElectricCurrentUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of ...
    """

    cuba_key = CUBA.ELECTRIC_CURRENT_UNIT

    def __init__(self, name=None):
        super(ElectricCurrentUnit, self).__init__(name)
