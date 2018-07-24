from cuba import CUBA
from ..core.data_container import DataContainer


class Entity(DataContainer):
    """
    the basic ontologicial entity, a thing. BFO
    """

    cuba_key = CUBA.ENTITY

    def __init__(self, name=None):
        super(Entity, self).__init__(name)
