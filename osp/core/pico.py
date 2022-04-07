"""Pico is a commandline tool used to install ontologies."""

import argparse
import itertools
import logging
from enum import Enum
from typing import TYPE_CHECKING, Iterator

from osp.core.ontology.installation import OntologyInstallationManager

# import osp.core.warnings as warning_settings -> Not working with Python 3.6.
from . import warnings as warning_settings

if TYPE_CHECKING:
    from osp.core.ontology.namespace import OntologyNamespace

__all__ = ["install", "uninstall", "namespaces", "packages"]

logger = logging.getLogger(__name__)

ontology_installer = OntologyInstallationManager()


def install(*files: str, overwrite: bool = False) -> None:
    """Install ontologies.

    Args:
        files: Paths of `yml` files describing the ontologies to install.
        overwrite: Whether to overwrite already installed ontologies.
    """
    if overwrite:
        ontology_installer.install_overwrite(*files)
    else:
        ontology_installer.install(*files)


def uninstall(*package_names: str) -> None:
    """Uninstall ontologies.

    Args:
        package_names: Names of the ontology packages to uninstall.
    """
    ontology_installer.uninstall(*package_names)


def packages() -> Iterator[str]:
    """Returns the names of all installed packages."""
    return iter(ontology_installer.get_installed_packages())


def namespaces() -> Iterator["OntologyNamespace"]:
    """Returns namespace objects for all the installed namespaces."""
    return iter(ontology_installer.namespace_registry)


def terminal():
    """Terminal interface for pico."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Install and uninstall your ontologies."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        help="Set the logging level",
    )
    subparsers = parser.add_subparsers(title="command", dest="command")

    # install parser
    install_parser = subparsers.add_parser(
        "install", help="Install ontologies."
    )
    install_parser.add_argument(
        "files", nargs="+", type=str, help="List of yaml files to install"
    )
    install_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing ontologies, "
        "if they are already installed",
    )

    # uninstall parser
    uninstall_parser = subparsers.add_parser(
        "uninstall", help="Uninstall ontologies."
    )
    uninstall_parser.add_argument(
        "packages",
        nargs="+",
        type=str,
        help="List of ontology packages to uninstall",
    )

    # list parser
    subparsers.add_parser("list", help="List all installed ontologies.")

    args = parser.parse_args()
    logging.getLogger("osp.core").setLevel(getattr(logging, args.log_level))
    logging.getLogger("osp.core.ontology.installation").setLevel(
        getattr(logging, args.log_level)
    )

    # Force RDF properties warning when running from the terminal and do not
    # offer the option to disable it.
    warning_settings.rdf_properties_warning = None

    try:
        all_namespaces = map(lambda x: x.get_name(), namespaces())
        all_packages = packages()
        if args.command == "install" and args.overwrite:
            install(*args.files, overwrite=True)
        elif args.command == "install":
            install(*args.files, overwrite=False)
        elif args.command == "uninstall":
            if args.packages == ["all"]:
                args.packages = all_packages
            uninstall(*args.packages)
        elif args.command == "list":
            print("Packages:")
            print("\n".join(map(lambda x: "\t- " + x, all_packages)))
            print("Namespaces:")
            print("\n".join(map(lambda x: "\t- " + x, all_namespaces)))
    except Exception:
        logger.error("An Exception occurred during installation.", exc_info=1)
        if args.log_level != "DEBUG":
            logger.error(
                "Consider running 'pico --log-level debug %s ...'"
                % args.command
            )


class CompareOperations(Enum):
    """The allowed values for the compare_version function."""

    leq: str = "leq"
    l: str = "l"


def compare_version(
    version,
    other_version,
    operation: CompareOperations = CompareOperations.leq,
):
    """Compares two software version strings.

    Receives two software version strings which are just numbers separated by
    dots and determines whether the first one is less or equal than the
    second one.

    Args:
        version (str): first version string (number separated by dots).
        other_version (str): second version string (number separated by dots).
        operation (str): the comparison operation to perform. The default is
            `leq` (less or equal).

    Returns:
        bool: whether the first version string is less or equal than the second
        one.
    """
    version = map(int, version.split("."))
    other_version = map(int, other_version.split("."))
    for v, o in itertools.zip_longest(version, other_version, fillvalue=0):
        if v == o:
            continue
        return v < o
    else:
        return operation == CompareOperations.leq


if __name__ == "__main__":
    terminal()
