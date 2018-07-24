from cuba import CUBA
from mesoscopic_entity import MesoscopicEntity


class UnitedAtom(MesoscopicEntity):
    """
    To Be Determined
    """

    cuba_key = CUBA.UNITED_ATOM

    def __init__(self, name=None):
        super(UnitedAtom, self).__init__(name)
