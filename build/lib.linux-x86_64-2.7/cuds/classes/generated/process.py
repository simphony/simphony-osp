from cuba import CUBA
from occurrent import Occurrent


class Process(Occurrent):
    """
    bfo
    """

    cuba_key = CUBA.PROCESS

    def __init__(self, name=None):
        super(Process, self).__init__(name)
