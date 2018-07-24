from cuba import CUBA
from continuant import Continuant


class IndependentContinuant(Continuant):
    """
    bfo
    """

    cuba_key = CUBA.INDEPENDENT_CONTINUANT

    def __init__(self, name=None):
        super(IndependentContinuant, self).__init__(name)
