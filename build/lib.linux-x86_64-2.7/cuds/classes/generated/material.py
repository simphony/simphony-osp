from cuba import CUBA
from material_entity import MaterialEntity


class Material(MaterialEntity):
    """
    a material (materials science) and its properties in the data
    container
    """

    cuba_key = CUBA.MATERIAL

    def __init__(self, name=None):
        super(Material, self).__init__(name)
