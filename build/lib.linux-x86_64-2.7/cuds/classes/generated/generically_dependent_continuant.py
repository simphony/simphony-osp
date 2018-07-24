from cuba import CUBA
from continuant import Continuant


class GenericallyDependentContinuant(Continuant):
    """
    bfo
    """

    cuba_key = CUBA.GENERICALLY_DEPENDENT_CONTINUANT

    def __init__(self, name=None):
        super(GenericallyDependentContinuant, self).__init__(name)
