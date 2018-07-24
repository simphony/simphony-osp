from cuba import CUBA
from interatomic_potential import InteratomicPotential


class PairPotential(InteratomicPotential):
    """
    Pair Interatomic Potential
    """

    cuba_key = CUBA.PAIR_POTENTIAL

    def __init__(self, name=None):
        super(PairPotential, self).__init__(name)
