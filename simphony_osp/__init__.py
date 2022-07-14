"""SimPhoNy OSP module."""

from importlib import import_module as _import_module

_import_module("simphony_osp.utils.pico")  # Load installed ontologies

__all__ = [
    "ontology",
    "session",
    "tools",
    "development",
    "namespaces",
    "wrappers",
]
