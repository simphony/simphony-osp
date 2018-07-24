from cuba import CUBA
from datum_label import DatumLabel


class DatumUnitLabel(DatumLabel):
    """
    A datum label that designates a relative measure of a datum quantity
    """

    cuba_key = CUBA.DATUM_UNIT_LABEL

    def __init__(self, name=None):
        super(DatumUnitLabel, self).__init__(name)
