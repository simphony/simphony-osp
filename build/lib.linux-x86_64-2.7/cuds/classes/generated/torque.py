from cuba import CUBA
from quality import Quality


class Torque(Quality):
    """
    mechanical toruque
    """

    cuba_key = CUBA.TORQUE

    def __init__(self, name=None):
        super(Torque, self).__init__(name)
