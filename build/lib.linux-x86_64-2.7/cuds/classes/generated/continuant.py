from cuba import CUBA
from cuds_entity import CudsEntity


class Continuant(CudsEntity):
    """
    BFO continuant
    """

    cuba_key = CUBA.CONTINUANT

    def __init__(self, name=None):
        super(Continuant, self).__init__(name)
