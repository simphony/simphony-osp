from cuba import CUBA
from model_entity import ModelEntity


class Molecule(ModelEntity):
    """
    To Be Determined
    """

    cuba_key = CUBA.MOLECULE

    def __init__(self, name=None):
        super(Molecule, self).__init__(name)
