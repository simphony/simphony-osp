"""Pico is a commandline tool used to install ontologies."""

from enum import Enum
import argparse
import logging
import itertools
from osp.core.ontology.installation import OntologyInstallationManager

logger = logging.getLogger(__name__)


def install_from_terminal():
    """Install ontologies from terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Install and uninstall your ontologies."
    )
    parser.add_argument("--log-level", default="INFO", type=str.upper,
                        help="Set the logging level")
    subparsers = parser.add_subparsers(
        title="command", dest="command"
    )

    # install parser
    install_parser = subparsers.add_parser(
        "install",
        help="Install ontologies."
    )
    install_parser.add_argument(
        "files", nargs="+", type=str, help="List of yaml files to install"
    )
    install_parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite the existing ontologies, if they are already installed"
    )

    # uninstall parser
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall ontologies."
    )
    uninstall_parser.add_argument(
        "packages", nargs="+", type=str,
        help="List of ontology packages to uninstall"
    )

    # list parser
    subparsers.add_parser(
        "list",
        help="List all installed ontologies."
    )

    args = parser.parse_args()
    logging.getLogger("osp.core").setLevel(getattr(logging, args.log_level))

    ontology_installer = OntologyInstallationManager()

    try:
        all_namespaces = map(lambda x: x.get_name(),
                             ontology_installer.namespace_registry)
        all_packages = ontology_installer.get_installed_packages()
        if args.command == "install" and args.overwrite:
            ontology_installer.install_overwrite(*args.files)
        elif args.command == "install":
            ontology_installer.install(*args.files)
        elif args.command == "uninstall":
            if args.packages == ['all']:
                args.packages = all_packages
            ontology_installer.uninstall(*args.packages)
        elif args.command == "list":
            print("Packages:")
            print("\n".join(map(lambda x: "\t- " + x, all_packages)))
            print("Namespaces:")
            print("\n".join(map(lambda x: "\t- " + x, all_namespaces)))
    except Exception:
        logger.error("An Exception occurred during installation.", exc_info=1)
        if args.log_level != "DEBUG":
            logger.error("Consider running 'pico --log-level debug %s ...'"
                         % args.command)


if __name__ == "__main__":
    install_from_terminal()
