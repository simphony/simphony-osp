"""You can import the installed namespaces from this module."""

import logging as _logging
from typing import TYPE_CHECKING as _TYPE_CHECKING
from typing import Union as _Union

from rdflib import URIRef as _URIRef
from rdflib.term import Identifier as _Identifier

from simphony_osp.session.session import Session as _Session
from simphony_osp.utils.pico import (
    OntologyInstallationManager as _OntologyInstallationManager,
)

if _TYPE_CHECKING:
    from simphony_osp.ontology.entity import OntologyEntity

self = __import__(__name__)

_logger = _logging.getLogger(__name__)

# --- Load installed ontologies --
# Set ontology directory and create it if nonexistent

# Load the ontologies.
_default_ontology = _Session.ontology
try:
    # Sort installed ontologies for loading (topological sort).
    _InstallationManager = _OntologyInstallationManager()
    _parsers = _InstallationManager.topologically_sorted_parsers

    # Load installed ontologies.
    for _parser in _parsers:
        _default_ontology.load_parser(_parser)
except RuntimeError:
    _logger.critical("Could not load installed ontologies.", exc_info=1)


# Access namespaces from this module.


def __getattr__(name: str):
    try:
        return _Session.ontology.get_namespace(name)
    except KeyError as e:
        raise AttributeError from e


def __dir__():
    return list((x.name for x in _Session.ontology.namespaces))


__all__ = __dir__()


# `from_iri` as gateway to `_tbox.from_identifier`.
def from_iri(iri: _Union[str, _URIRef]):
    """Get an entity from its IRI from the default TBox.

    Args:
        iri: The IRI of the entity.

    Raises:
        KeyError: The ontology entity is not stored in the default TBox.

    Returns:
        The OntologyEntity.
    """
    if type(iri) is str:
        iri = _URIRef(str)
    if not isinstance(iri, _URIRef):
        raise TypeError(f"Expected {str} or {_URIRef}, not {type(iri)}.")
    return _Session.ontology.from_identifier(iri)


# `from_identifier` as gateway to `_tbox.from_identifier`.
def from_identifier(identifier: _Identifier) -> "OntologyEntity":
    """Get an entity from its identifier from the default TBox.

    Args:
        identifier: The identifier of the entity.

    Raises:
        KeyError: The ontology entity is not stored in the default TBox.

    Returns:
        The OntologyEntity.
    """
    return _Session.ontology.from_identifier(identifier)
