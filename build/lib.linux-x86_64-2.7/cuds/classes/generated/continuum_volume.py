from cuba import CUBA
from continuum_entity import ContinuumEntity


class ContinuumVolume(ContinuumEntity):
    """
    To Be Determined
    """

    cuba_key = CUBA.CONTINUUM_VOLUME

    def __init__(self, name=None):
        super(ContinuumVolume, self).__init__(name)
