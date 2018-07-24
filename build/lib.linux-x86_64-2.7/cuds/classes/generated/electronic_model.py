from cuba import CUBA
from physics_based_model import PhysicsBasedModel


class ElectronicModel(PhysicsBasedModel):
    """
    physics-based model based on a physics equation describing the
    behaviour of electron entities
    """

    cuba_key = CUBA.ELECTRONIC_MODEL

    def __init__(self, name=None):
        super(ElectronicModel, self).__init__(name)
