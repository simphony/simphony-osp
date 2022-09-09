"""Pico is a tool used to install ontologies."""

import argparse
import logging
from pathlib import Path
from typing import Tuple, Union

from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.utils.pico import logger, pico

__all__ = ["packages", "namespaces", "install", "uninstall"]


def packages() -> Tuple[str]:
    """Returns the identifiers of all installed packages."""
    return pico.packages


def namespaces() -> Tuple[OntologyNamespace]:
    """Returns namespace objects for all the installed namespaces."""
    return pico.namespaces


def install(*files: Union[Path, str], overwrite: bool = False) -> None:
    """Install ontology packages.

    Args:
        files: Paths of ontology packages to install. Alternatively,
            identifiers of ontology packages that are bundled with SimPhoNy.
        overwrite: Whether to overwrite already installed ontology
            packages.
    """
    return pico.install(*files, overwrite=overwrite)


def uninstall(*identifiers: str) -> None:
    """Uninstall ontology packages.

    Args:
        identifiers: Identifiers of the ontology packages to uninstall.
    """
    return pico.uninstall(*identifiers)


def terminal() -> None:
    """Install ontologies from the terminal."""
    # Entry point
    parser = argparse.ArgumentParser(
        description="This tool manages the ontologies used by SimPhoNy."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        help="set the logging level",
    )

    # --- Available commands ---
    subparsers = parser.add_subparsers(title="command", dest="command")

    # list
    subparsers.add_parser("list", help="Lists all the installed ontologies")

    # install
    install_parser = subparsers.add_parser(
        "install", help="Install ontologies"
    )
    install_parser.add_argument(
        "files", nargs="+", type=str, help="List of yaml files to install"
    )
    install_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing ontologies, if they are already "
        "installed",
    )

    # uninstall parser
    uninstall_parser = subparsers.add_parser(
        "uninstall", help="Uninstall ontologies"
    )
    uninstall_parser.add_argument(
        "packages",
        nargs="+",
        type=str,
        help="List of ontology packages to uninstall",
    )

    args = parser.parse_args()
    logging.getLogger("simphony_osp").setLevel(
        getattr(logging, args.log_level)
    )

    try:
        installed_identifiers = list(pico.packages)
        if args.command == "install" and args.overwrite:
            pico.install(*args.files, overwrite=True)
        elif args.command == "install":
            pico.install(*args.files, overwrite=False)
        elif args.command == "uninstall":
            if args.packages == ["all"]:
                args.packages = installed_identifiers
            pico.uninstall(*args.packages)
        elif args.command == "list":
            print("Packages:")
            print("\n".join(map(lambda x: "\t- " + x, installed_identifiers)))

            installed_namespaces = tuple(
                namespace.name for namespace in pico.ontology.namespaces
            )
            print("Namespaces:")
            print("\n".join(map(lambda x: "\t- " + x, installed_namespaces)))
    except Exception:
        logger.error("An Exception occurred during installation.", exc_info=1)
        if args.log_level != "DEBUG":
            logger.error(
                "Consider running 'pico --log-level debug %s ...'"
                % args.command
            )


if __name__ == "__main__":
    terminal()
