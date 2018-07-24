from cuba import CUBA
from mesoscopic_entity import MesoscopicEntity


class SphericalParticle(MesoscopicEntity):
    """
    To Be Determined
    """

    cuba_key = CUBA.SPHERICAL_PARTICLE

    def __init__(self, name=None):
        super(SphericalParticle, self).__init__(name)
