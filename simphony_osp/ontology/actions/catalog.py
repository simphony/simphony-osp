"""Implements a catalog of available actions for ontology individuals."""

from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from rdflib import URIRef

__all__ = ["register"]

_catalog: Dict[URIRef, Dict[str, Tuple[Type, Callable]]] = dict()


def get(item: Union[str, URIRef], default: Optional[Any] = None):
    item = URIRef(item)
    return _catalog.get(item, default)


def register(class_: Type, identifier: str):
    """Register an `Actions` object in the catalog."""
    identifier = URIRef(identifier)

    # Look for actions defined on the class
    methods = {
        name: method
        for name, method in class_.__dict__.items()
        if hasattr(method, "_is_simphony_action")
        and getattr(method, "_is_simphony_action") is True
    }

    catalog_entry = _catalog.get(identifier, dict())

    # Raise exception if two methods with the same name are registered
    conflicts = set(catalog_entry) & set(methods)
    if conflicts:
        raise RuntimeError(
            f"Methods {','.join(conflicts)} defined twice for class "
            f"{identifier}."
        )

    # Put the actions on the catalog
    catalog_entry.update(
        {name: (class_, method) for name, method in methods.items()}
    )
    _catalog[identifier] = catalog_entry
