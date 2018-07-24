from cuba import CUBA
from atomistic_entity import AtomisticEntity


class Atom(AtomisticEntity):
    """
    Atom
    """

    cuba_key = CUBA.ATOM

    def __init__(self, name=None):
        super(Atom, self).__init__(name)
