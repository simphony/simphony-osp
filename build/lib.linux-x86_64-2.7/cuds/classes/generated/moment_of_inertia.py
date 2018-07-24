from cuba import CUBA
from quality import Quality


class MomentOfInertia(Quality):
    """
    the moment of intertia
    """

    cuba_key = CUBA.MOMENT_OF_INERTIA

    def __init__(self, name=None):
        super(MomentOfInertia, self).__init__(name)
