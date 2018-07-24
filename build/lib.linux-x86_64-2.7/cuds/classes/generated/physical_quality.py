from cuba import CUBA
from determinate import Determinate


class PhysicalQuality(Determinate):
    """
    PATO, A quality of a physical entity that exists through action of
    continuants at the physical level of organisation in relation to other
    entities. ROMM, CWA, Physics QUANTITY
    """

    cuba_key = CUBA.PHYSICAL_QUALITY

    def __init__(self, value, name=None):
        super(PhysicalQuality, self).__init__(value, name)
