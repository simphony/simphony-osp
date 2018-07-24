from cuba import CUBA
from physical_quality import PhysicalQuality


class Energy(PhysicalQuality):
    """
    energy
    """

    cuba_key = CUBA.ENERGY

    def __init__(self, value, name=None):
        super(Energy, self).__init__(value, name)
