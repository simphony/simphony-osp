from cuba import CUBA
from immaterial_entity import ImmaterialEntity


class ContinuantFiatBoundary(ImmaterialEntity):
    """
    bfo
    """

    cuba_key = CUBA.CONTINUANT_FIAT_BOUNDARY

    def __init__(self, name=None):
        super(ContinuantFiatBoundary, self).__init__(name)
