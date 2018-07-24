from cuba import CUBA
from material_entity import MaterialEntity


class Object(MaterialEntity):
    """
    bfo
    """

    cuba_key = CUBA.OBJECT

    def __init__(self, name=None):
        super(Object, self).__init__(name)
