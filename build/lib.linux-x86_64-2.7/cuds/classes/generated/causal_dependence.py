from cuba import CUBA
from causal_relation import CausalRelation


class CausalDependence(CausalRelation):
    """
    causal dependence relating to multiple entities and qualities, for
    example the reciprocal causal dependence between the pressure and
    temperature of a portion of gas;
    """

    cuba_key = CUBA.CAUSAL_DEPENDENCE

    def __init__(self, name=None):
        super(CausalDependence, self).__init__(name)
