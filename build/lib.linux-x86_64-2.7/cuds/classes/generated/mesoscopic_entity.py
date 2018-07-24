from cuba import CUBA
from model_entity import ModelEntity


class MesoscopicEntity(ModelEntity):
    """
    a representation of a set of bounded atoms (e.g. group of atoms,
    molecule, bead, cluster)
    """

    cuba_key = CUBA.MESOSCOPIC_ENTITY

    def __init__(self, name=None):
        super(MesoscopicEntity, self).__init__(name)
