from cuba import CUBA
from thermostat import Thermostat


class TemperatureRescaling(Thermostat):
    """
    A simple temperature rescaling thermostat. The coupling time specifies
    how offen the temperature should be relaxed or coupled to the bath.
    """

    cuba_key = CUBA.TEMPERATURE_RESCALING

    def __init__(self, name=None):
        super(TemperatureRescaling, self).__init__(name)
