import shutil
import logging
import os
import logging as _logging
import atexit as _atexit
from osp.core.owl_ontology.owl_namespace_registry import NamespaceRegistry \
    as _NamespaceRegistry

_logger = _logging.getLogger(__name__)

# load installed ontologies
_namespace_registry = _NamespaceRegistry()
_path = os.path.join(
    os.path.expanduser("~"),
    ".osp_ontologies"
)
_installed_path = os.path.join(_path, "installed")
_current_path = _installed_path
os.makedirs(_installed_path, exist_ok=True)


def _clean():
    if _current_path != _installed_path:
        _logger.info("Removing %s" % _current_path)
        shutil.rmtree(_current_path)


try:
    _namespace_registry.load(_installed_path)
except RuntimeError:
    _logger.critical("Could not load installed ontologies.", exc_info=1)
_atexit.register(lambda: _clean())


def __getattr__(name):
    return getattr(_namespace_registry, name)
