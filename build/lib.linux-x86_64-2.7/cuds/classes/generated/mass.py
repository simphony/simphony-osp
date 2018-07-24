from cuba import CUBA
from quality import Quality


class Mass(Quality):
    """
    mass of an entity
    """

    cuba_key = CUBA.MASS

    def __init__(self, value, name=None):
        super(Mass, self).__init__(name)

        self.value = value
