from cuba import CUBA
from quality import Quality


class AngularVelocity(Quality):
    """
    angular velocity of an entity
    """

    cuba_key = CUBA.ANGULAR_VELOCITY

    def __init__(self, name=None):
        super(AngularVelocity, self).__init__(name)
