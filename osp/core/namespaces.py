import sys as _sys
import logging as _logging
import atexit as _atexit
from osp.core.owl_ontology.owl_namespace_registry import NamespaceRegistry \
    as _NamespaceRegistry
from osp.core.owl_ontology.owl_initializer import OntologyInitializer \
    as _OntologyInitializer

_logger = _logging.getLogger(__name__)

# load installed ontologies
_thismodule = _sys.modules[__name__]
_namespace_registry = _NamespaceRegistry()
# _owl_initializer = _OntologyInitializer(_namespace_registry)

# try:
#     _owl_initializer.initialize_installed_ontologies(_thismodule)
# except RuntimeError:
#     _logger.critical("Could not load installed ontologies.", exc_info=1)
# _atexit.register(lambda: _owl_initializer._clean())


def __getattr__(name):
    return getattr(_namespace_registry, name)
