from cuba import CUBA
from material_entity import MaterialEntity


class FiatObjectPart(MaterialEntity):
    """
    bfo
    """

    cuba_key = CUBA.FIAT_OBJECT_PART

    def __init__(self, name=None):
        super(FiatObjectPart, self).__init__(name)
