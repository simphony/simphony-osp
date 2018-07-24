from cuba import CUBA
from physics_based_equation import PhysicsBasedEquation


class MaterialRelation(PhysicsBasedEquation):
    """
    To Be Determined
    """

    cuba_key = CUBA.MATERIAL_RELATION

    def __init__(self, name=None):
        super(MaterialRelation, self).__init__(name)
