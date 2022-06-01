"""Classes supporting the definition and use of custom operations in SimPhoNy.

This file contains an `Operations` abstract class that wrapper or package
developers can use to implement specific functionality for certain ontology
classes (e.g. download and upload commands for files, multiplying EMMO
vectors, ...).

Instances of the `OperationsNamespace` class are accessed as the `operations`
property of ontology individuals. The `OperationsNamespace` instances let the
user access the operations defined for each ontology individual. Each
individual has an associated instance of the subclass of `Operations` that the
wrapper or package developer has defined.
"""
from __future__ import annotations

import os
import pkgutil
import sys
from abc import ABC, abstractmethod
from collections.abc import Mapping
from functools import wraps
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from simphony_osp.ontology.operations import catalog

if TYPE_CHECKING:
    from simphony_osp.ontology import OntologyIndividual


__all__ = [
    "Operations",
    "OperationsNamespace",
    "find_operations_in_package",
    "find_operations_in_operations_folder",
    "find_operations",
]


class Operations(ABC):
    """Define operations for an ontology class."""

    @property
    @abstractmethod
    def iri(self) -> Union[str, Iterable[str]]:
        """IRI of the ontology class for which operations should be registered.

        It is also possible to define several IRIs at once (by returning an
        iterable).
        """
        pass

    def __init__(self, individual: OntologyIndividual):
        """Initialization of your instance of the operations.

        It is recommended to save the individual that is received as an
        argument to an instance attribute, as the operations to be executed are
        supposed to be related to it.
        """
        self._individual = individual

    @classmethod
    def __simphony_operations__(cls) -> Dict[str, Union[Callable, property]]:
        """Magic method that returns the operations defined on this class."""
        dir_operations = dir(Operations)
        methods = {
            name: getattr(cls, name)
            for name in dir(cls)
            if not (name.startswith("_") or name in dir_operations)
        }
        return methods


class OperationsNamespace(Mapping):
    """Access the operations associated to an ontology individual.

    Instances of the `OperationsNamespace` class are accessed as the
    `operations` property of ontology individuals. The `OperationsNamespace`
    instances let the user access the operations defined for each ontology
    individual. Each individual has an associated instance of the subclass of
    `Operations` that the wrapper or package developer has defined.
    """

    _individual: OntologyIndividual
    _instances: Dict[Type, Operations]

    def __init__(self, individual: OntologyIndividual):
        """Initialize the `OperationsNamespace`."""
        self._instances = dict()
        self._individual = individual

    def __getattr__(self, item: str):
        """Get an operation by name using dot notation."""
        try:
            result = self[item]
        except KeyError as e:
            raise AttributeError(str(e)) from e
        return result

    def __getitem__(self, key: str) -> Callable:
        """Get an operation by name using brackets."""
        results = {
            (class_, method)
            for name, class_, method in self._all_methods
            if name == key
        }
        if len(results) > 1:
            raise RuntimeError(
                f"More than one operation available under the name {key} for "
                f"individual {self._individual} of classes "
                f"{','.join(str(x) for x in self._individual.classes)} "
                f"available ."
            )
        elif len(results) == 0:
            raise KeyError(
                f"No operation with name {key} available for "
                f"{self._individual} of classes "
                f"{','.join(str(x) for x in self._individual.classes)}."
            )
        class_, method = results.pop()
        instance = self._instances.get(class_) or class_(
            individual=self._individual
        )

        if isinstance(method, property):
            result = getattr(instance, key)
        else:

            @wraps(method)
            def function(*args, **kwargs):
                return method(instance, *args, **kwargs)

            result = function

        return result

    def __len__(self) -> int:
        """Number of operations available for the individual."""
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator[str]:
        """Iterate over the names of the available operations."""
        yield from {name for name, class_, method in self._all_methods}

    @property
    def _all_methods(self) -> Set[Tuple[str, Type, Callable]]:
        """Get a set will all the available operations for the individual."""
        classes = (
            class_.identifier for class_ in self._individual.superclasses
        )
        results = {
            (name, class_, method)
            for identifier in classes
            for name, (class_, method) in catalog.get(
                identifier, dict()
            ).items()
        }
        return results


OPERATIONS = TypeVar("OPERATIONS", bound=Operations)


def find_operations_in_package(
    path: Union[str, Path]
) -> Generator[Type[OPERATIONS]]:
    """Find operations on a Python package.

    Given the path of a Python package (a folder containing an `__init__.py`
    file), this function finds all the operations defined in the package
    and yields them back.

    Args:
        path: location of the Python package to be scanned for operation
            definitions.

    Yields:
        Operation definitions, that is, subclasses of the `Operations` class.
    """
    package_paths = [path]

    def load_submodules_recursively(paths: List[str]) -> Iterator[ModuleType]:
        """Load Python packages and all of their submodules.

        Given the paths of Python packages, this function loads the package as
        well as all the submodules recursively.

        Args:
            paths: Paths of the Python packages to load.

        Yields:
            The loaded Python modules.
        """
        pathlib_paths = [Path(x) for x in paths]
        names = {
            module_info.name
            for module_info in pkgutil.iter_modules(
                str(x.parent.absolute()) for x in pathlib_paths
            )
            if module_info.ispkg
            and module_info.name in {x.name for x in pathlib_paths}
        }
        filter_walk = (
            (loader, module_name, is_pkg)
            for loader, module_name, is_pkg in pkgutil.walk_packages(
                str(x.parent.absolute()) for x in pathlib_paths
            )
            if any(module_name.startswith(name) for name in names)
        )

        for loader, module_name, is_pkg in filter_walk:
            if module_name not in sys.modules:
                spec = loader.find_spec(module_name)
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[module_name] = module
                yield module
            else:
                yield sys.modules[module_name]

    modules = load_submodules_recursively(package_paths)
    modules = {module.__name__ for module in modules}
    classes = (
        x for x in Operations.__subclasses__() if x.__module__ in modules
    )
    return classes


def find_operations_in_operations_folder(
    path: Union[str, Path]
) -> Set[Type[OPERATIONS]]:
    """Find operation definitions in a folder.

    Given a folder path, this function scans the folder for operation
    definitions and returns them.

    Args:
        path: The folder path to be scanned.

    Returns:
        A set of operation definitions, that is, subclasses of the
        `Operations` class.
    """
    package_paths = [path]
    prefix = "simphony_osp.ontology.operations.installed."

    for loader, module_name, is_pkg in pkgutil.walk_packages(
        package_paths, prefix
    ):
        if module_name not in sys.modules:
            spec = loader.find_spec(module_name)
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[module_name] = module
    return {
        operation
        for operation in Operations.__subclasses__()
        if operation.__module__.startswith(prefix)
    }


def find_operations(
    packages: Optional[Union[List[str], str]] = None,
) -> Set[str]:
    """Generates the entry point definitions for operations.

    Scans one or several packages and generates sets of strings that can be
    used in `setup.py` to register SimPhoNy ontology operations.

    This method is meant to ease the work that operation developers have to
    do in their `setup.py` files.

    Args:
        packages: name(s) of the package(s) to scan. When left empty,
            all packages on the working directory are scanned.

    Returns:
        Set of strings that can be used with the
        "simphony_osp.ontology.operations" entry point.

        Example:
            {"File = simphony_osp.ontology.operations.file:File"}
    """
    if isinstance(packages, str):
        packages = [packages]

    path = Path(os.getcwd()).absolute()
    packages = packages or []

    paths = [path / package for package in packages] or [
        path / module_info.name
        for module_info in pkgutil.iter_modules([str(path)])
        if module_info.ispkg
    ]

    operations = {
        op for path in paths for op in find_operations_in_package(path)
    }

    operations = {
        f"{op.__name__} = {op.__module__}:{op.__name__}" for op in operations
    }

    return operations
