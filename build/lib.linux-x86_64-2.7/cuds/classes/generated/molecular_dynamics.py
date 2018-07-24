from cuba import CUBA
from physics_based_model import PhysicsBasedModel


class MolecularDynamics(PhysicsBasedModel):
    """
    To Be Determined
    """

    cuba_key = CUBA.MOLECULAR_DYNAMICS

    def __init__(self, name=None):
        super(MolecularDynamics, self).__init__(name)
