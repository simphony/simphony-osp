from cuba import CUBA
from quality import Quality


class VolumeFraction(Quality):
    """
    the portion of mater in a unit volume of the material.
    """

    cuba_key = CUBA.VOLUME_FRACTION

    def __init__(self, name=None):
        super(VolumeFraction, self).__init__(name)
