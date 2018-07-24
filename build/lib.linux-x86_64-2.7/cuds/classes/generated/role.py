from cuba import CUBA
from realizable_entity import RealizableEntity


class Role(RealizableEntity):
    """
    BFO
    """

    cuba_key = CUBA.ROLE

    def __init__(self, name=None):
        super(Role, self).__init__(name)
