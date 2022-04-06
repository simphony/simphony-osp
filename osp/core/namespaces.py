"""You can import the installed namespaces from this module."""

import logging as _logging
import os as _os

from osp.core.ontology.installation import (
    OntologyInstallationManager as _OntologyInstallationManager,
)
from osp.core.ontology.namespace_registry import (
    namespace_registry as _namespace_registry,
)

_logger = _logging.getLogger(__name__)

# load installed ontologies
_path = _OntologyInstallationManager.get_default_installation_path()
_os.makedirs(_path, exist_ok=True)


try:
    _namespace_registry.load_graph_file(_path)
except RuntimeError:
    _logger.critical("Could not load installed ontologies.", exc_info=1)


def get_entity(name):
    """Get an entity by the given name.

    Args:
        name (str): namespace.entity_name

    Returns:
        OntologyEntity: The entity with the given name.
    """
    ns, n = name.split(".")
    return _namespace_registry._get(ns)._get(n)


from_iri = _namespace_registry.from_iri

__getattr__ = _namespace_registry.__getattr__
