from cuba import CUBA
from condition import Condition


class Thermostat(Condition):
    """
    A thermostat is a model that describes the thermal interaction of a
    material with the environment or a heat reservoir
    """

    cuba_key = CUBA.THERMOSTAT

    def __init__(self, name=None):
        super(Thermostat, self).__init__(name)
