from cuba import CUBA
from physical_quality import PhysicalQuality


class Hydrophilicity(PhysicalQuality):
    """
    A physical quality inhering in a bearer by virtue the bearer
    disposition to having an affinity for water; it is readily absorbing
    or dissolving in water.
    """

    cuba_key = CUBA.HYDROPHILICITY

    def __init__(self, value, name=None):
        super(Hydrophilicity, self).__init__(value, name)
