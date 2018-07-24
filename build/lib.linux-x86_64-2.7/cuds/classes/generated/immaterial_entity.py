from cuba import CUBA
from independent_continuant import IndependentContinuant


class ImmaterialEntity(IndependentContinuant):
    """
    bfo
    """

    cuba_key = CUBA.IMMATERIAL_ENTITY

    def __init__(self, name=None):
        super(ImmaterialEntity, self).__init__(name)
