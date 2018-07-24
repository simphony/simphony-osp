from cuba import CUBA
from independent_continuant import IndependentContinuant


class MaterialEntity(IndependentContinuant):
    """
    bfo
    """

    cuba_key = CUBA.MATERIAL_ENTITY

    def __init__(self, name=None):
        super(MaterialEntity, self).__init__(name)
