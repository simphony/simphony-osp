import sys
import atexit
from osp.core.ontology.installation import OntologyInstallationManager

thismodule = sys.modules[__name__]
ONTOLOGY_INSTALLER = OntologyInstallationManager()
try:
    ONTOLOGY_INSTALLER.initialize_installed_ontologies(thismodule)
except RuntimeError as e:
    print("Could not load installed ontologies:")
    print(e)
atexit.register(ONTOLOGY_INSTALLER._clean)

user_defined_default_rel = None
installed_default_rel = ONTOLOGY_INSTALLER.namespace_registry.default_rel


def get_entity(entity_name):
    namespace, name = ONTOLOGY_INSTALLER.parser.split_name(entity_name)
    return ONTOLOGY_INSTALLER.namespace_registry[namespace][name]


def install_current_ontology():
    ONTOLOGY_INSTALLER.install()

from osp.core.ontology.parser import Parser
