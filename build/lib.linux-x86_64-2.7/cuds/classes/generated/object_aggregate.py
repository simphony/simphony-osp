from cuba import CUBA
from material_entity import MaterialEntity


class ObjectAggregate(MaterialEntity):
    """
    bfo
    """

    cuba_key = CUBA.OBJECT_AGGREGATE

    def __init__(self, name=None):
        super(ObjectAggregate, self).__init__(name)
