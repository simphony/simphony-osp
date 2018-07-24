from cuba import CUBA
from material_entity import MaterialEntity


class ModelEntity(MaterialEntity):
    """
    CWA, self-contained, internally frozen, structure-less
    representational unit of a material
    """

    cuba_key = CUBA.MODEL_ENTITY

    def __init__(self, name=None):
        super(ModelEntity, self).__init__(name)
