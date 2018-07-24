from cuba import CUBA
from molecule import Molecule


class MesoscopicMolecule(Molecule):
    """
    To Be Determined
    """

    cuba_key = CUBA.MESOSCOPIC_MOLECULE

    def __init__(self, name=None):
        super(MesoscopicMolecule, self).__init__(name)
