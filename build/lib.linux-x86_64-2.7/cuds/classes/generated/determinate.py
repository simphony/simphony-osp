from cuba import CUBA
from determinable import Determinable


class Determinate(Determinable):
    """
    bfo, some quality that can be determined such as temperature, mass.
    Note this is equivalent to r instance of universal spatial region with
    volume w == soatrial region r has volume w.
    """

    cuba_key = CUBA.DETERMINATE

    def __init__(self, value, name=None):
        super(Determinate, self).__init__(name)

        self.value = value
