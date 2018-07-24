from cuba import CUBA
from physics_equation import PhysicsEquation


class NewtonClassicalEquation(PhysicsEquation):
    """
    To Be Determined
    """

    cuba_key = CUBA.NEWTON_CLASSICAL_EQUATION

    def __init__(self, name=None):
        super(NewtonClassicalEquation, self).__init__(name)
