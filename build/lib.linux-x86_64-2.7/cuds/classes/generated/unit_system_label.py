from cuba import CUBA
from datum_label import DatumLabel


class UnitSystemLabel(DatumLabel):
    """
    see NASA QUDT, a label designating a unit system used to specify
    determinables
    """

    cuba_key = CUBA.UNIT_SYSTEM_LABEL

    def __init__(self, name=None):
        super(UnitSystemLabel, self).__init__(name)
