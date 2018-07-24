from cuba import CUBA
from model_entity import ModelEntity


class AtomisticEntity(ModelEntity):
    """
    a representation of an atom [SOURCE IEV 113-05-20]
    """

    cuba_key = CUBA.ATOMISTIC_ENTITY

    def __init__(self, name=None):
        super(AtomisticEntity, self).__init__(name)
