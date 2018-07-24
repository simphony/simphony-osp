from cuba import CUBA
from model_entity import ModelEntity


class ContinuumEntity(ModelEntity):
    """
    a representation of the material bounded in a region of space within
    which the material is considered by the modeller to be described by
    the same set of properties
    """

    cuba_key = CUBA.CONTINUUM_ENTITY

    def __init__(self, name=None):
        super(ContinuumEntity, self).__init__(name)
