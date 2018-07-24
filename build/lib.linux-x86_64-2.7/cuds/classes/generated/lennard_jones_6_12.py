from cuba import CUBA
from pair_potential import PairPotential


class LennardJones612(PairPotential):
    """
    A Lennard-Jones 6-12 Potential
    """

    cuba_key = CUBA.LENNARD_JONES_6_12

    def __init__(self, name=None):
        super(LennardJones612, self).__init__(name)
