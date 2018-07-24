from cuba import CUBA
from specifically_dependent_continuant import SpecificallyDependentContinuant


class RealizableEntity(SpecificallyDependentContinuant):
    """
    BFO
    """

    cuba_key = CUBA.REALIZABLE_ENTITY

    def __init__(self, name=None):
        super(RealizableEntity, self).__init__(name)
