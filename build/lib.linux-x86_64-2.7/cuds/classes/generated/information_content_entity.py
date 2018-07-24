from cuba import CUBA
from generically_dependent_continuant import GenericallyDependentContinuant


class InformationContentEntity(GenericallyDependentContinuant):
    """
    BFO-IAO, a generically dependent continuant that is about some thing.
    """

    cuba_key = CUBA.INFORMATION_CONTENT_ENTITY

    def __init__(self, name=None):
        super(InformationContentEntity, self).__init__(name)
