from cuba import CUBA
from physics_based_model import PhysicsBasedModel


class ModelEquation(PhysicsBasedModel):
    """
    To Be Determined
    """

    cuba_key = CUBA.MODEL_EQUATION

    def __init__(self, name=None):
        super(ModelEquation, self).__init__(name)
