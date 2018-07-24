from cuba import CUBA
from immaterial_entity import ImmaterialEntity


class Site(ImmaterialEntity):
    """
    bfo
    """

    cuba_key = CUBA.SITE

    def __init__(self, name=None):
        super(Site, self).__init__(name)
