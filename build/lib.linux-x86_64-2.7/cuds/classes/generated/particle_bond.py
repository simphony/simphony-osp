from cuba import CUBA
from cuds_entity import CudsEntity


class ParticleBond(CudsEntity):
    """
    A bond between two or more atoms or particles
    """

    cuba_key = CUBA.PARTICLE_BOND

    def __init__(self, name=None):
        super(ParticleBond, self).__init__(name)
