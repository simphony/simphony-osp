from cuba import CUBA
from occurrent import Occurrent


class ProcessBoundary(Occurrent):
    """
    bfo
    """

    cuba_key = CUBA.PROCESS_BOUNDARY

    def __init__(self, name=None):
        super(ProcessBoundary, self).__init__(name)
