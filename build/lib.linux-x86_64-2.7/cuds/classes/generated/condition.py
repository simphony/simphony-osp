from cuba import CUBA
from causal_dependence import CausalDependence


class Condition(CausalDependence):
    """
    Condition on boundaries or model entities (ie., part of the physics
    equation add ons)
    """

    cuba_key = CUBA.CONDITION

    def __init__(self, name=None):
        super(Condition, self).__init__(name)
