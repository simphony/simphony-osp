from cuba import CUBA
from physical_quality import PhysicalQuality


class Charge(PhysicalQuality):
    """
    To Be Determined
    """

    cuba_key = CUBA.CHARGE

    def __init__(self, value, name=None):
        super(Charge, self).__init__(value, name)
