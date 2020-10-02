"""You can import the installed namespaces from this module."""

import os as _os
import logging as _logging
import rdflib
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
    """Get an entity by the given name.

    Args:
        name (str): namespace.entity_name

    Returns:
        OntologyEntity: The entity with the given name.
    """
    ns, n = name.split(".")
    return _namespace_registry._get(ns)._get(n)


def from_iri(iri, raise_error=True,
             allow_types=frozenset({rdflib.OWL.DatatypeProperty,
                                    rdflib.OWL.ObjectProperty,
                                    rdflib.OWL.Class})):
    """Get an OntologyEntity from its IRI.

    Args:
        iri (rdflib.URIRef): The IRI of the entity to load.
        raise_error (bool, optional): Whether to raise an error if the IRI
            is unknown. Defaults to True.
        allow_types (Set[rdflib.URIRef], optional): The allowed types of
            entities to load. Defaults to
                frozenset({rdflib.OWL.DatatypeProperty,
                           rdflib.OWL.ObjectProperty,
                           rdflib.OWL.Class}).

    Returns:
        OntologyEntity: The ontology entity with the given IRI.
    """
    return _namespace_registry.from_iri(iri, raise_error, allow_types)


def __getattr__(name):
    """Load an installed namespace.

    Args:
        name (str): The name of the namespace.

    Returns:
        OntologyNamespace: The namespace the user wanted to import.
    """
    return getattr(_namespace_registry, name)
