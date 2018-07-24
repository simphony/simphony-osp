from cuba import CUBA
from cuds import Cuds


class ParticleAggrgate(Cuds):
    """
    To Be Determined
    """

    cuba_key = CUBA.PARTICLE_AGGRGATE

    def __init__(self, name=None):
        super(ParticleAggrgate, self).__init__(name)
