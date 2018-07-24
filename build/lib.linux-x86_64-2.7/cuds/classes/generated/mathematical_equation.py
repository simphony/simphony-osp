from cuba import CUBA
from causal_relation import CausalRelation


class MathematicalEquation(CausalRelation):
    """
    a mathematical equation
    """

    cuba_key = CUBA.MATHEMATICAL_EQUATION

    def __init__(self, name=None):
        super(MathematicalEquation, self).__init__(name)
