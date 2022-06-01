"""Implements a catalog of available operations for ontology individuals."""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Tuple,
    Type,
    Union,
)

from rdflib import URIRef

if TYPE_CHECKING:
    from simphony_osp.ontology.operations.operations import Operations

__all__ = ["get", "register"]

_catalog: Dict[URIRef, Dict[str, Tuple[Type, Callable]]] = dict()


def get(
    item: Union[str, URIRef], default: Optional[Any] = None
) -> Union[Dict[str, Tuple[Type, Callable]], Any]:
    """Get the methods registered for the given identifier.

    Args:
        item: Identifier to get the methods for.
        default: Default value to return when the identifier is not registered.

    Raises:
        KeyError: Identifier not registered and no default provided.
    """
    item = URIRef(item)
    return _catalog.get(item, default)


def register(
    class_: Type[Operations], identifier: Union[str, Iterable[str]]
) -> None:
    """Register an `Operations` class in the catalog.

    Args:
        class_: The `Operations` class to register.
        identifier: The identifier (or identifiers) that will be
            registered as associated with the given `Operations` class.

    Raises:
        RuntimeError: Tried to register two methods with the same name for the
            same identifier.
    """
    identifiers = (
        (URIRef(identifier),) if isinstance(identifier, str) else identifier
    )

    methods = class_.__simphony_operations__()

    for identifier in identifiers:
        catalog_entry = _catalog.get(identifier, dict())

        # Raise exception if two methods with the same name are registered
        conflicts = set(catalog_entry) & set(methods)
        if conflicts:
            raise RuntimeError(
                f"Methods {','.join(conflicts)} defined twice for class "
                f"{identifier}."
            )

        # Put the operations on the catalog
        catalog_entry.update(
            {name: (class_, method) for name, method in methods.items()}
        )
        _catalog[identifier] = catalog_entry
