import os as _os
import logging as _logging
import rdflib
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


def get_entity(name):
    ns, n = name.split(".")
    return _namespace_registry._get(ns)._get(n)


def from_iri(iri, raise_error=True,
             allow_types=frozenset({rdflib.OWL.DatatypeProperty,
                                    rdflib.OWL.ObjectProperty,
                                    rdflib.OWL.Class})):
    return _namespace_registry.from_iri(iri, raise_error, allow_types)


def __getattr__(name):
    return getattr(_namespace_registry, name)
