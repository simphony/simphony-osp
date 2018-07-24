from cuba import CUBA
from thermostat import Thermostat


class Berendsen(Thermostat):
    """
    The Berendsen thermostat model for temperature rescaling of all
    particles. The coupling time specifies how rapidly the temperature
    should be relaxed or coupled to the bath.
    """

    cuba_key = CUBA.BERENDSEN

    def __init__(self, name=None):
        super(Berendsen, self).__init__(name)
