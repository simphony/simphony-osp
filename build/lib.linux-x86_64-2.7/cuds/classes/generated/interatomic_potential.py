from cuba import CUBA
from material_relation import MaterialRelation


class InteratomicPotential(MaterialRelation):
    """
    Interatomic Potentials
    """

    cuba_key = CUBA.INTERATOMIC_POTENTIAL

    def __init__(self, name=None):
        super(InteratomicPotential, self).__init__(name)
