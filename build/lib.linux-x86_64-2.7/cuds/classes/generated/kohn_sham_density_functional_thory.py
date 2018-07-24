from cuba import CUBA
from electronic_model import ElectronicModel


class KohnShamDensityFunctionalThory(ElectronicModel):
    """
    KS_DFT
    """

    cuba_key = CUBA.KOHN_SHAM_DENSITY_FUNCTIONAL_THORY

    def __init__(self, name=None):
        super(KohnShamDensityFunctionalThory, self).__init__(name)
