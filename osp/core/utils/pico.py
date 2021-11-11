"""Pico is a commandline tool used to install ontologies."""

import glob
import os
from typing import Optional

import argparse
import logging
from typing import List, Set, Tuple, Hashable

from osp.core.ontology.parser import OntologyParser

logger = logging.getLogger(__name__)


class OntologyInstallationManager:
    """This class handles the installation of ontologies."""

    path: str = os.path.join(
        os.environ.get("OSP_ONTOLOGIES_DIR") or os.path.expanduser("~"),
        ".osp_ontologies")

    def __init__(self,
                 path: Optional['str'] = None):
        """Initialize the installer.

        Args:
            ontology: The session to which the installed ontologies will be
                added. Defaults to the default ontology.
            path: Installation destination. When unspecified, the default
                location specified as a class variable is used.
        """
        if path is not None:
            self.path = path
        os.makedirs(self.path, exist_ok=True)

    @property
    def installed_packages(self) -> Tuple[Tuple[str, str], ...]:
        """Get the list of installed packages.

        Returns:
            A tuple of two-component tuples, where the first element is the
            identifier of the ontology packages and the second their path.
        """
        paths = tuple(os.path.join(self.path, yml) for yml in
                      (x for x in os.listdir(self.path)
                       if 'yml' in os.path.splitext(x)[1]))
        parsers = (OntologyParser.get_parser(path) for path in paths)
        return tuple((parser.identifier, path)
                     for parser, path in zip(parsers, paths))

    def install(self,
                *files: str,
                overwrite: bool = False):
        """Install given packages. Skip already installed ones.

        Args:
            files: The ontology files to install.
            overwrite: Whether to overwrite already installed packages.
        """
        installed_identifiers_and_paths = self.installed_packages
        installed_identifiers, _ = zip(*installed_identifiers_and_paths) \
            if installed_identifiers_and_paths else (tuple(), tuple())
        installed_identifiers = set(installed_identifiers)
        del installed_identifiers_and_paths
        new_parsers = {OntologyParser.get_parser(path) for path in files}
        new_identifiers = {parser.identifier for parser in new_parsers}
        install_parsers = {parser for parser in new_parsers
                           if parser.identifier not in installed_identifiers} \
            if not overwrite else new_parsers
        for identifier in new_identifiers & new_parsers:
            logger.info("Skipping package with identifier %s, "
                        "because it is already installed."
                        % identifier)
        del new_parsers, new_identifiers

        # Check that dependencies of packages to be installed are satisfied.
        install_identifiers = set(parser.identifier
                                  for parser in install_parsers)
        required_identifiers = set(requirement
                                   for parser in install_parsers
                                   for requirement in parser.requirements)
        missing_requirements = required_identifiers - \
            (installed_identifiers | install_identifiers)
        if missing_requirements:
            missing_requirements_dict = dict()
            for parser in install_parsers:
                missing = tuple(x in missing_requirements
                                for x in parser.requirements)
                if missing:
                    missing_requirements_dict[parser.identifier] = missing
            raise RuntimeError(
                "Installation failed. Unsatisfied requirements: \n - %s"
                % "\n - ".join(["%s: %s" % (n, r)
                                for n, r in missing_requirements_dict.items()])
            )

        if installed_identifiers:
            logger.info("The following packages are already installed: %s."
                        % ', '.join(installed_identifiers))
        if install_identifiers:
            logger.info("Will install the following packages: %s."
                        % ', '.join(install_identifiers))
            logger.info("Will install the following namespaces: %s."
                        % ', '.join(name
                                    for parser in install_parsers
                                    for name in parser.namespaces.keys()))

        for parser in install_parsers:
            parser.install(self.path)

        logger.info("Installation successful")

    def uninstall(self, *files_or_packages):
        """Uninstall given packages."""
        remove_parsers = {OntologyParser.get_parser(path)
                          for path in files_or_packages}
        remove_identifiers = {parser.identifier for parser in remove_parsers}
        existing_identifiers = {identifier
                                for identifier, _ in self.installed_packages}

        non_installed_identifiers = remove_identifiers - existing_identifiers
        if non_installed_identifiers:
            raise RuntimeError(f"Cannot uninstall the following packages, "
                               f"as they are not installed: "
                               f"{', '.join(non_installed_identifiers)}.")

        files_to_remove = (
            glob.glob(os.path.join(self.path, f'{identifier}*'))
            for identifier in remove_identifiers)
        files_to_remove = set(file
                              for glob_list in files_to_remove
                              for file in glob_list)
        for file in files_to_remove:
            os.remove(file)

        logger.info("Uninstallation successful")

    @property
    def topologically_sorted_parsers(self) -> List[OntologyParser]:
        """Returns a list of parsers, topologically sorted.

        As the parsers are topologically sorted with respect to their
        requirements, they can be loaded in order without triggering missing
        ontology entity errors.
        """
        paths = {os.path.join(self.path, yml) for yml in
                 (x for x in os.listdir(self.path)
                  if 'yml' in os.path.splitext(x)[1])}
        parsers = {OntologyParser.get_parser(path) for path in paths}
        directed_edges = {(requirement, parser.identifier)
                          for parser in parsers
                          for requirement in parser.requirements or (None,)}
        sorted_identifiers = topological_sort(directed_edges)
        parsers = sorted(parsers,
                         key=lambda x: sorted_identifiers.index(x.identifier))
        return parsers


def pico():
    """Install ontologies from the terminal."""
    # Entry point
    parser = argparse.ArgumentParser(
        description="This tool enables to manage the ontologies used by "
                    "OSP-core."
    )
    parser.add_argument("--log-level",
                        default="INFO",
                        type=str.upper,
                        help="set the logging level")

    # --- Available commands ---
    subparsers = parser.add_subparsers(
        title="command",
        dest="command"
    )

    # list
    subparsers.add_parser(
        "list",
        help="Lists all the installed ontologies"
    )

    # install
    install_parser = subparsers.add_parser(
        "install",
        help="Install ontologies"
    )
    install_parser.add_argument(
        "files",
        nargs="+",
        type=str,
        help="List of yaml files to install"
    )
    install_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing ontologies, if they are already installed"
    )

    # uninstall parser
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall ontologies"
    )
    uninstall_parser.add_argument(
        "packages",
        nargs="+",
        type=str,
        help="List of ontology packages to uninstall"
    )

    args = parser.parse_args()
    logging.getLogger("osp.core").setLevel(getattr(logging, args.log_level))

    ontology_installer = OntologyInstallationManager()

    try:
        installed_identifiers = [identifier
                                 for identifier, _
                                 in ontology_installer.installed_packages]
        if args.command == "install" and args.overwrite:
            ontology_installer.install(*args.files, overwrite=True)
        elif args.command == "install":
            ontology_installer.install(*args.files, overwrite=False)
        elif args.command == "uninstall":
            if args.packages == ['all']:
                args.packages = [identifier
                                 for identifier, _
                                 in ontology_installer.installed_packages]
            ontology_installer.uninstall(*args.packages)
        elif args.command == "list":
            print("Packages:")
            print("\n".join(map(lambda x: "\t- " + x, installed_identifiers)))
            from osp.core.session.session import Session
            installed_namespaces = tuple(namespace.name
                                         for namespace in
                                         Session.ontology.namespaces)
            print("Namespaces:")
            print("\n".join(map(lambda x: "\t- " + x, installed_namespaces)))
    except Exception:
        logger.error("An Exception occurred during installation.", exc_info=1)
        if args.log_level != "DEBUG":
            logger.error("Consider running 'pico --log-level debug %s ...'"
                         % args.command)


def topological_sort(edges: Set[Tuple[Hashable, Hashable]]):
    """Kanh's algorithm for topological sort.

    Kahn, Arthur B. (1962), "Topological sorting of large networks",
    Communications of the ACM, 5 (11): 558–562, doi:10.1145/368996.369025,
    S2CID 16728233

    Args:
        edges: A set of directed edge pairs (the first element is the tail
            and the second the head).
    """
    # Structure the graph as a dict for fast lookup.
    graph = dict()
    for x, y in edges:
        if x not in graph:
            graph[x] = {y}
        else:
            graph[x] |= {y}
        if y not in graph:
            graph[y] = set()

    result = []
    no_incoming_edges = set(graph.keys()) - {x for s in graph.values()
                                             for x in s}
    while no_incoming_edges:
        node = no_incoming_edges.pop()
        result += [node]
        for m in set(graph[node]):
            graph[node].remove(m)
            if m not in {x for s in graph.values() for x in s}:
                no_incoming_edges.add(m)

    if {y for x in graph.values() for y in x}:
        raise ValueError("The provided set of edges has cycles, therefore "
                         "topological sorting is unfeasible.")
    return tuple(result)


if __name__ == "__main__":
    pico()
