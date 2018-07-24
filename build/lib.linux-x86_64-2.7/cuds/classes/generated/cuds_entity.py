from cuba import CUBA
from entity import Entity


class CudsEntity(Entity):
    """
    Root of all CUDS classes
    """

    cuba_key = CUBA.CUDS_ENTITY

    def __init__(self, name=None):
        super(CudsEntity, self).__init__(name)
