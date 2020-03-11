import sys
import atexit
import logging

logging.getLogger("rdflib").setLevel(logging.WARNING)

from osp.core.packageinfo import VERSION as __version__
from osp.core.ontology.installation import OntologyInstallationManager

# set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(levelname)s [%(name)s]: %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)

# load installed ontologies
thismodule = sys.modules[__name__]
ONTOLOGY_INSTALLER = OntologyInstallationManager()
try:
    ONTOLOGY_INSTALLER.initialize_installed_ontologies(thismodule)
except RuntimeError as e:
    logger.critical("Could not load installed ontologies.", exc_info=1)
atexit.register(ONTOLOGY_INSTALLER._clean)

IRI_DOMAIN = "http://www.osp-core.com"

# utility functions
def get_entity(entity_name):
    namespace, name = ONTOLOGY_INSTALLER.parser.split_name(entity_name)
    return ONTOLOGY_INSTALLER.namespace_registry[namespace][name]


def install_current_ontology():
    ONTOLOGY_INSTALLER.install()

from osp.core.ontology.parser import Parser
