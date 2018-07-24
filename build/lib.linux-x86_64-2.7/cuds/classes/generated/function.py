from cuba import CUBA
from disposition import Disposition


class Function(Disposition):
    """
    BFO
    """

    cuba_key = CUBA.FUNCTION

    def __init__(self, name=None):
        super(Function, self).__init__(name)
