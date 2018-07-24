from cuba import CUBA
from molecule import Molecule


class AtomisticMolecule(Molecule):
    """
    To Be Determined
    """

    cuba_key = CUBA.ATOMISTIC_MOLECULE

    def __init__(self, name=None):
        super(AtomisticMolecule, self).__init__(name)
