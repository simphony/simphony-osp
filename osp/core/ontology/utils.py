"""Utility resources for the ontology module."""

import functools
import importlib
import os
import pkgutil
from typing import Any, Dict, Tuple

from osp.core.ontology.entity import OntologyEntity

"""Define a `compatible_classes` function that lists the Python classes that
can be spawned for a particular RDF.type and type of node identifier.

This function used by `osp.core.session.Session.from_identifier` to
determine which Python class should be spawned for a given IRI or BNode.

Read the docstrings of the functions defined in this section for more details.
"""
# ↓ --------------- ↓


@functools.lru_cache(maxsize=None)
def _compute_mappings() -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    """Maps RDF types and node identifier types to Python classes.

    The classes defined in OSP-core that are meant to represent ontology
    entities (all subclasses of `OntologyEntity`), have two attributes,
    `rdf_type` and `rdf_identifier` that determine the combination of RDF
    types (e.g. owl:Class) and node identifier types (e.g. URIRef, BNode) that
    the class is meant to represent.

    This function imports the `osp.core.ontology` module and all of its
    submodules recursively, as all subclasses of `OntologyEntity` are
    expected to be stored there.

    After that, it generates two mappings, `mapping_rdf_to_python_class` and
    `mapping_identifier_to_python_class`, that map each rdf type and node
    identifier type to compatible Python classes.

    Using such mappings, other functions can find out the compatible classes
    for a specific pair of RDF type and node identifier type.

    This function is cached, as it is called by `compatible_classes`
    repeatedly, but the computation is only needed once. In fact, this code
    could be defined outside of a function, but it has been incorporated
    into a function because of the need to evaluate it lazily (to avoid
    circular imports).

    Returns:
        A tuple `mapping_rdf_to_python_class,
        mapping_identifier_to_python_class` containing the aforementioned
        mappings.
    """
    # First, import the ontology module and all of its submodules recursively.
    self = __import__(__name__)
    package_paths = [
        os.path.abspath(
            os.path.join(path, 'core/ontology')
        )
        for path in self.__path__
    ]
    package_prefix = f'{self.__name__}.core.ontology.'

    def import_modules_recursively(paths, prefix):
        for module_info in pkgutil.iter_modules(
                paths,
                prefix
        ):
            module = importlib.import_module(module_info.name)
            if module_info.ispkg:
                import_modules_recursively(module.__path__,
                                           f'{module_info.name}.')

    import_modules_recursively(package_paths, package_prefix)

    # Then compute the mappings, remember that the python class to instantiate
    # for a given ontology entity depends on two things:
    # - The RDF.type(s) of the identifier.
    # - The RDF node type of the identifier (URIRef, Node or Literal)

    mapping_rdf_to_python_class = dict()
    mapping_identifier_to_python_class = dict()

    def recursive_iterator(class_):
        for sub_class in class_.__subclasses__():
            yield from recursive_iterator(sub_class)
            yield sub_class

    for subclass in recursive_iterator(OntologyEntity):
        rdf_types = subclass.rdf_type \
            if isinstance(subclass.rdf_type, set) else {subclass.rdf_type}
        for rdf_type in rdf_types:
            mapping_rdf_to_python_class[rdf_type] = \
                mapping_rdf_to_python_class.get(rdf_type, set()) | {subclass}
        rdf_identifiers = subclass.rdf_identifier \
            if isinstance(subclass.rdf_identifier, set) \
            else {subclass.rdf_identifier}
        for rdf_identifier in rdf_identifiers:
            mapping_identifier_to_python_class[rdf_identifier] = \
                mapping_identifier_to_python_class.get(rdf_identifier, set()) \
                | {subclass}
    return mapping_rdf_to_python_class, mapping_identifier_to_python_class


def compatible_classes(type_, identifier):
    """Given a pair of a RDF type and an identifier get a Python class.

    Given a pair of a RDF type and an identifier, the compatible Python
    classes are computed. In fact, for the latter only the type of
    identifier matters.
    """
    mapping_rdf_to_python_class, mapping_identifier_to_python_class = \
        _compute_mappings()
    # Remember that the call above is cached (see `_compute_mappings`).

    from_type = mapping_rdf_to_python_class.get(type_, set())
    from_identifier = functools.reduce(
        lambda x, y: x | y,
        (value
         for key, value in mapping_identifier_to_python_class.items()
         if isinstance(identifier, key)),
        set()
    )
    return from_type & from_identifier

# ↑ --------------- ↑
