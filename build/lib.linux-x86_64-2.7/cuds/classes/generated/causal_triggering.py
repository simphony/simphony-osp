from cuba import CUBA
from causal_relation import CausalRelation


class CausalTriggering(CausalRelation):
    """
    causal triggering, where a process is the trigger for a second process
    which is the realization of a disposition.
    """

    cuba_key = CUBA.CAUSAL_TRIGGERING

    def __init__(self, name=None):
        super(CausalTriggering, self).__init__(name)
