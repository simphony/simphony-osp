from cuba import CUBA
from model_entity import ModelEntity


class ElectronicEntity(ModelEntity):
    """
    CWA, a representation of an electron [SOURCE IEV 113-05-18]
    """

    cuba_key = CUBA.ELECTRONIC_ENTITY

    def __init__(self, name=None):
        super(ElectronicEntity, self).__init__(name)
