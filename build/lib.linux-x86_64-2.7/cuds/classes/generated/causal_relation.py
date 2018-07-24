from cuba import CUBA
from occurrent import Occurrent


class CausalRelation(Occurrent):
    """
    relations between entities and qualities like equations expressing
    some fundamental truth about the behaviour of the entities within a
    certain  view of the world
    """

    cuba_key = CUBA.CAUSAL_RELATION

    def __init__(self, name=None):
        super(CausalRelation, self).__init__(name)
