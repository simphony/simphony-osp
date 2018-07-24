from cuba import CUBA
from quality import Quality


class Determinable(Quality):
    """
    bfo, some quality that can be determined such as temperature, mass
    """

    cuba_key = CUBA.DETERMINABLE

    def __init__(self, name=None):
        super(Determinable, self).__init__(name)
