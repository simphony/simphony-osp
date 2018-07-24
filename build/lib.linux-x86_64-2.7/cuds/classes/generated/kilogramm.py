from cuba import CUBA
from mass_unit import MassUnit


class Kilogramm(MassUnit):
    """
    The kilogram (symbol, kg), used to measure mass defined as...
    """

    cuba_key = CUBA.KILOGRAMM

    def __init__(self, name=None):
        super(Kilogramm, self).__init__(name)
