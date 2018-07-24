from cuba import CUBA
from quality import Quality


class RelationalQuality(Quality):
    """
    BFO
    """

    cuba_key = CUBA.RELATIONAL_QUALITY

    def __init__(self, name=None):
        super(RelationalQuality, self).__init__(name)
