from cuba import CUBA
from cuds_entity import CudsEntity


class Occurrent(CudsEntity):
    """
    bfo
    """

    cuba_key = CUBA.OCCURRENT

    def __init__(self, name=None):
        super(Occurrent, self).__init__(name)
