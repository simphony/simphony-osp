from cuba import CUBA
from physical_quality import PhysicalQuality


class Temperature(PhysicalQuality):
    """
    To Be Determined
    """

    cuba_key = CUBA.TEMPERATURE

    def __init__(self, value, name=None):
        super(Temperature, self).__init__(value, name)
