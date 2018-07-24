from cuba import CUBA
from object_aggregate import ObjectAggregate


class Cuds(ObjectAggregate):
    """
    A material system representation using CUDS objects. Can be seen as
    either ICE or a material aggregate represented as a Data Container
    i.e., a knowledge-based data object of semantic concepts used to
    agglomerate relevant data and information. An aggregate object or
    object in the BFO sense.
    """

    cuba_key = CUBA.CUDS

    def __init__(self, name=None):
        super(Cuds, self).__init__(name)
