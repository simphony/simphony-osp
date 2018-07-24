from cuba import CUBA
from physics_based_model import PhysicsBasedModel


class AtomisticModel(PhysicsBasedModel):
    """
    physics-based model based on a physics equation describing the
    behaviour of atom entities
    """

    cuba_key = CUBA.ATOMISTIC_MODEL

    def __init__(self, name=None):
        super(AtomisticModel, self).__init__(name)
