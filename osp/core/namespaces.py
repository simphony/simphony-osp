"""You can import the installed namespaces from this module."""

import logging as _logging
import os as _os
from typing import Union as _Union
from typing import TYPE_CHECKING as _TYPE_CHECKING

from rdflib import URIRef as _URIRef
from rdflib.term import Identifier as _Identifier

from osp.core.ontology.installation import topological_sort as \
    _topological_sort
from osp.core.ontology.parser import OntologyParser as _OntologyParser
from osp.core.session.session import Session as _Session

if _TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity

self = __import__(__name__)

_logger = _logging.getLogger(__name__)

# --- Load installed ontologies --
# Set ontology directory and create it if nonexistent
_osp_ontologies_dir = _os.environ.get("OSP_ONTOLOGIES_DIR") \
    or _os.path.expanduser("~")
_path = _os.path.join(
    _osp_ontologies_dir,
    ".osp_ontologies"
)
_os.makedirs(_path, exist_ok=True)
# Load the ontologies.
_default_ontology = _Session.ontology
try:
    # Load built-in ontologies.
    _parser = _OntologyParser.get_parser('cuba')
    _default_ontology.load_parser(_parser)
    _parser = _OntologyParser.get_parser('owl')
    _default_ontology.load_parser(_parser)

    # Sort installed ontologies for loading (topological sort).
    _paths = {_os.path.join(_path, _yml) for _yml in
              (x for x in _os.listdir(_path)
               if 'yml' in _os.path.splitext(x)[1])}
    _parsers = {_OntologyParser.get_parser(path) for path in _paths}
    _directed_edges = {(requirement, parser.identifier)
                       for parser in _parsers
                       for requirement in parser.requirements or (None, )}
    _sorted_identifiers = _topological_sort(_directed_edges)
    _parsers = sorted(_parsers,
                      key=lambda x: _sorted_identifiers.index(x.identifier))

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


# `from_iri` as gateway to `_tbox.from_identifier`.
def from_iri(iri: _Union[str, _URIRef]):
    if type(iri) is str:
        iri = _URIRef(str)
    if not isinstance(iri, _URIRef):
        raise TypeError(f"Expected {str} or {_URIRef}, not {type(iri)}.")
    return _Session.ontology.from_identifier(iri)


# `from_identifier` as gateway to `_tbox.from_identifier`.
def from_identifier(identifier: _Identifier) -> 'OntologyEntity':
    return _Session.ontology.from_identifier(identifier)
