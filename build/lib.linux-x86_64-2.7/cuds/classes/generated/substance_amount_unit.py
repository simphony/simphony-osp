from cuba import CUBA
from datum_unit_label import DatumUnitLabel


class SubstanceAmountUnit(DatumUnitLabel):
    """
    A unit which is a standard measure of ...
    """

    cuba_key = CUBA.SUBSTANCE_AMOUNT_UNIT

    def __init__(self, name=None):
        super(SubstanceAmountUnit, self).__init__(name)
