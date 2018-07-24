from cuba import CUBA
from process import Process


class ProcessProfile(Process):
    """
    bfo
    """

    cuba_key = CUBA.PROCESS_PROFILE

    def __init__(self, name=None):
        super(ProcessProfile, self).__init__(name)
