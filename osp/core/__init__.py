import sys
import atexit
from osp.core.ontology.installation import OntologyInstallationManager

thismodule = sys.modules[__name__]
ONTOLOGY_INSTALLER = OntologyInstallationManager()
ONTOLOGY_INSTALLER.initialize_installed_ontologies(thismodule)
atexit.register(ONTOLOGY_INSTALLER._clean)

user_defined_default_rel = None
installed_default_rel = ONTOLOGY_INSTALLER.namespace_registry.default_rel


def get_default_rel():
    global user_defined_default_rel, installed_default_rel

    result = (
        user_defined_default_rel
        or ONTOLOGY_INSTALLER.namespace_registry.default_rel
        or installed_default_rel
    )
    user_defined_default_rel = result
    return result


def set_default_rel(rel):
    global user_defined_default_rel
    user_defined_default_rel = rel


def get_entity(entity_name):
    namespace, name = ONTOLOGY_INSTALLER.parser.split_name(entity_name)
    return ONTOLOGY_INSTALLER.namespace_registry[namespace][name]


def install_current_ontology():
    ONTOLOGY_INSTALLER.install()

from osp.core.ontology.parser import Parser
