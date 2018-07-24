from cuba import CUBA
from mathematical_equation import MathematicalEquation


class PhysicsBasedEquation(MathematicalEquation):
    """
    mathematical equation based on a fundamental physics theory which
    defines the relations between physics quantities of an entity
    """

    cuba_key = CUBA.PHYSICS_BASED_EQUATION

    def __init__(self, name=None):
        super(PhysicsBasedEquation, self).__init__(name)
