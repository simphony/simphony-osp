from cuba import CUBA
from mesoscopic_entity import MesoscopicEntity


class CoarsegrainedAtom(MesoscopicEntity):
    """
    To Be Determined
    """

    cuba_key = CUBA.COARSEGRAINED_ATOM

    def __init__(self, name=None):
        super(CoarsegrainedAtom, self).__init__(name)
