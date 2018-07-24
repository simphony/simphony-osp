from cuba import CUBA
from electronic_entity import ElectronicEntity


class Electron(ElectronicEntity):
    """
    a representation of an electron
    """

    cuba_key = CUBA.ELECTRON

    def __init__(self, name=None):
        super(Electron, self).__init__(name)
