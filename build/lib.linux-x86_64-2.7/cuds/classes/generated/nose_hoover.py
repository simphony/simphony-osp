from cuba import CUBA
from thermostat import Thermostat


class NoseHoover(Thermostat):
    """
    Add an extra term to the equation of motion to model the interaction
    with an external heat bath. The coupling time specifies how rapidly
    the temperature should be coupled to the bath.
    """

    cuba_key = CUBA.NOSE_HOOVER

    def __init__(self, name=None):
        super(NoseHoover, self).__init__(name)
