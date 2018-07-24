from cuba import CUBA
from physical_quality import PhysicalQuality


class Force(PhysicalQuality):
    """
    To Be Determined
    """

    cuba_key = CUBA.FORCE

    def __init__(self, value, name=None):
        super(Force, self).__init__(value, name)
