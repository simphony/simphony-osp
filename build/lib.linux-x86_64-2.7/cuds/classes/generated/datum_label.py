from cuba import CUBA
from information_content_entity import InformationContentEntity


class DatumLabel(InformationContentEntity):
    """
    A label is a symbol that is part of some other datum and is used to
    either partially define  the denotation of that datum or to provide a
    means for identifying the datum as a member of the set of data with
    the same label
    """

    cuba_key = CUBA.DATUM_LABEL

    def __init__(self, name=None):
        super(DatumLabel, self).__init__(name)
