from cuba import CUBA
from realizable_entity import RealizableEntity


class Disposition(RealizableEntity):
    """
    BFO
    """

    cuba_key = CUBA.DISPOSITION

    def __init__(self, name=None):
        super(Disposition, self).__init__(name)
