from cuba import CUBA
from quality import Quality


class DynamicPressure(Quality):
    """
    the time changing force per unit area on a surface
    """

    cuba_key = CUBA.DYNAMIC_PRESSURE

    def __init__(self, name=None):
        super(DynamicPressure, self).__init__(name)
