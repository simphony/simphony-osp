import os as _os
import logging as _logging
from osp.core.ontology.namespace_registry import NamespaceRegistry \
    as _NamespaceRegistry

_logger = _logging.getLogger(__name__)

# load installed ontologies
_osp_ontologies_dir = _os.environ.get("OSP_ONTOLOGIES_DIR") \
    or _os.path.expanduser("~")
_namespace_registry = _NamespaceRegistry()
_path = _os.path.join(
    _osp_ontologies_dir,
    ".osp_ontologies"
)
_os.makedirs(_path, exist_ok=True)


try:
    _namespace_registry.load(_path)
except RuntimeError:
    _logger.critical("Could not load installed ontologies.", exc_info=1)


def get_entity(name):
    ns, n = name.split(".")
    return _namespace_registry._get(ns)._get(n)


def from_iri(iri):
    return _namespace_registry.from_iri(iri)


def __getattr__(name):
    return getattr(_namespace_registry, name)
