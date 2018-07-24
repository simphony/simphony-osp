from cuba import CUBA
from continuant import Continuant


class SpecificallyDependentContinuant(Continuant):
    """
    bfo
    """

    cuba_key = CUBA.SPECIFICALLY_DEPENDENT_CONTINUANT

    def __init__(self, name=None):
        super(SpecificallyDependentContinuant, self).__init__(name)
