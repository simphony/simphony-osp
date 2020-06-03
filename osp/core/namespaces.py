import os as _os
import logging as _logging
from osp.core.ontology.namespace_registry import NamespaceRegistry \
    as _NamespaceRegistry

_logger = _logging.getLogger(__name__)

# load installed ontologies
_namespace_registry = _NamespaceRegistry()
_path = _os.path.join(
    _os.path.expanduser("~"),
    ".osp_ontologies"
)
_os.makedirs(_path, exist_ok=True)


try:
    _namespace_registry.load(_path)
except RuntimeError:
    _logger.critical("Could not load installed ontologies.", exc_info=1)


def __getattr__(name):
    return getattr(_namespace_registry, name)
