from cuba import CUBA
from physics_based_equation import PhysicsBasedEquation


class PhysicsEquation(PhysicsBasedEquation):
    """
    mathematical equation based on a fundamental physics theory which
    defines the relations between physics quantities of an entity
    """

    cuba_key = CUBA.PHYSICS_EQUATION

    def __init__(self, name=None):
        super(PhysicsEquation, self).__init__(name)
