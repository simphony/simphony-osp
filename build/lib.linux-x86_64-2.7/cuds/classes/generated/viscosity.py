from cuba import CUBA
from physical_quality import PhysicalQuality


class Viscosity(PhysicalQuality):
    """
    To Be Determined
    """

    cuba_key = CUBA.VISCOSITY

    def __init__(self, value, name=None):
        super(Viscosity, self).__init__(value, name)
