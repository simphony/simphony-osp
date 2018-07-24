from cuba import CUBA
from specifically_dependent_continuant import SpecificallyDependentContinuant


class Quality(SpecificallyDependentContinuant):
    """
    BFO
    """

    cuba_key = CUBA.QUALITY

    def __init__(self, name=None):
        super(Quality, self).__init__(name)
