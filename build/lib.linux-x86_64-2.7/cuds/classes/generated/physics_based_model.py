from cuba import CUBA
from physics_based_equation import PhysicsBasedEquation


class PhysicsBasedModel(PhysicsBasedEquation):
    """
    solvable set of one physics equation and one or more materials
    relations
    """

    cuba_key = CUBA.PHYSICS_BASED_MODEL

    def __init__(self, name=None):
        super(PhysicsBasedModel, self).__init__(name)
