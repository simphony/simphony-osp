"""Pico is a tool to manage SimPhoNy's installed ontologies.

This file contains the non-public-facing elements of pico.
"""

import glob
import logging
import os
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Hashable,
    Iterable,
    Iterator,
    List,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)

HASHABLE = TypeVar("HASHABLE", bound=Hashable)


def graph_set_to_dict(
    arcs: Set[Tuple[HASHABLE, HASHABLE]]
) -> MutableMapping[HASHABLE, Set[HASHABLE]]:
    """Convert the graph from a set of arcs to a dictionary (fast lookup).

    Transforms a set of arcs into a dictionary of arcs.

    Args:
        arcs: A set of arcs (directed edges) represented by tuples, where
            their first element is the tail and the second the head.

    Returns:
        A dictionary of arcs, where the keys represent the tail of an arc
        and each value is a set of heads for such tail. Therefore,
        each key-value pair represents several arcs.
    """
    graph = dict()
    for x, y in arcs:
        if x not in graph:
            graph[x] = {y}
        else:
            graph[x] |= {y}
        if y not in graph:
            graph[y] = set()
    return graph


def depth_first_search(
    graph: MutableMapping[HASHABLE, Set[HASHABLE]],
    start: Iterable[HASHABLE],
    goal: Callable[[HASHABLE], bool],
) -> Iterator[HASHABLE]:
    """Implementation of depth first search graph algorithm.

    This implementation assumes that the provided set of arcs represents a
    directed graph. Arcs will only be traversed from their tails to their
    heads.

    This implementation is in the form of a generator. This means that the
    algorithm will look for a "goal" node, but instead of returning it,
    it will yield it. This implies that after returning the first node,
    if the iterator is called again, it will return more "goal" nodes that
    satisfy the goal function.

    Args:
        graph: A dictionary of arcs, where the keys represent the tail of an
            arc and each value is a set of heads for such tail. Therefore, each
            key-value pair represents several arcs.
        start: The starting nodes.
        goal: A function that evaluates at every node to determine whether
            it is a "goal" node (should be yielded) or not.

    Yields:
        Nodes that satisfy the goal condition.
    """
    visited = set()
    queue = list(set(start))
    while queue:
        node = queue.pop()
        if goal(node):
            yield node
        visited.add(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                queue.append(neighbor)


def topological_sort(graph: MutableMapping[Hashable, Set[Hashable]]):
    """Kanh's algorithm for topological sort.

    Kahn, Arthur B. (1962), "Topological sorting of large networks",
    Communications of the ACM, 5 (11): 558–562, doi:10.1145/368996.369025,
    S2CID 16728233

    Args:
        graph: A dictionary of arcs, where the keys represent the tail of an
            arc and each value is a set of heads for such tail. Therefore, each
            key-value pair represents several arcs.
    """
    result = []
    no_incoming_edges = set(graph.keys()) - {
        x for s in graph.values() for x in s
    }
    while no_incoming_edges:
        node = no_incoming_edges.pop()
        result += [node]
        for m in set(graph[node]):
            graph[node].remove(m)
            if m not in {x for s in graph.values() for x in s}:
                no_incoming_edges.add(m)

    if {y for x in graph.values() for y in x}:
        raise ValueError(
            "The provided set of arcs has cycles, therefore "
            "topological sorting is unfeasible."
        )
    return tuple(result)


class Pico:
    """This class manages the installed ontologies."""

    def __init__(self, path: Optional[Union[str, Path]] = None):
        """Initialize pico.

        Args:
            path: Installation destination. When unspecified, the default
                location is used.
        """
        self._ontology = Session(identifier="pico ontologies", ontology=True)
        os.makedirs(self.path, exist_ok=True)
        if path is not None:
            self.path = path
        self._reload_installed_ontologies()

    @property
    def ontology(self) -> Session:
        """Ontology containing all the installed packages.

        This ontology is reloaded every time a change in the installed
        ontologies is done through an instance of this class.

        WARNING: Be careful not to instantiate two instances of `Pico` using
        the same `path`.
        """
        return self._ontology

    @property
    def path(self) -> Path:
        """Path where ontologies are installed."""
        return self._path or self.get_default_installation_path()

    @path.setter
    def path(self, value: Optional[str]):
        """Set the path where ontologies are installed."""
        self._path = value if value is None else Path(value)
        self._reload_installed_ontologies()

    @property
    def packages(self) -> Tuple[str]:
        """Returns the identifiers of all installed packages."""
        return tuple(self._package_names)

    @property
    def namespaces(self) -> Tuple[OntologyNamespace]:
        """Returns namespace objects for all the installed namespaces."""
        return tuple(self.ontology.namespaces)

    def install(
        self, *files: Union[Path, str], overwrite: bool = False
    ) -> None:
        """Install ontology packages.

        Args:
            files: Paths of `yml` files describing the ontologies to install.
                Alternatively, identifiers of ontology packages that are
                bundled with SimPhoNy.
            overwrite: Whether to overwrite already installed ontology
                packages.
        """
        files: Tuple[Path] = tuple(Path(file) for file in files)
        installed_identifiers: Set[str] = set(self._package_names)
        new_parsers: Dict[str, Tuple[OntologyParser, Path]] = {
            parser.identifier: (parser, path)
            for path in files
            for parser in (OntologyParser.get_parser(path),)
        }
        new_identifiers = set(new_parsers)
        if overwrite:
            installed_identifiers -= new_identifiers
        skip_identifiers = new_identifiers & installed_identifiers
        install_parsers: Dict[str, Tuple[OntologyParser, Path]] = {
            identifier: (parser, path)
            for identifier, (parser, path) in new_parsers.items()
            if identifier not in skip_identifiers
        }
        for identifier in skip_identifiers:
            logger.info(
                "Skipping package with identifier %s, "
                "because it is already installed." % identifier
            )
        del new_parsers, new_identifiers, skip_identifiers

        # Resolve the dependencies using DFS with the goal function below.
        # - create requirements graph
        requirements_graph = {
            identifier: parser.requirements
            for identifier, (parser, path) in install_parsers.items()
        }
        missing_requirements = set()

        def explore_dependencies(node: str) -> False:
            """Generate the dependency graph.

            Goal function for the DFS algorithm that loads each
            package (if not loaded already or installed), evaluates its
            dependencies and adds them to the graph.

            When a package fails to load, it is added to a set of missing
            requirements, that is later used to raise an exception.
            """
            if (
                node not in installed_identifiers
                and node not in install_parsers
            ):
                try:
                    parser = OntologyParser.get_parser(node)
                    install_parsers[parser.identifier] = (parser, Path(node))
                    requirements_graph[node] = parser.requirements
                except FileNotFoundError:
                    requirements_graph[node] = set()
                    missing_requirements.add(node)
            return False

        depth_first_search_iterator = depth_first_search(
            requirements_graph, requirements_graph, explore_dependencies
        )
        # Since the goal function is always false, asking for the next item
        # is enough to explore the whole graph.
        next(depth_first_search_iterator, None)

        # Raise exception if there are missing requirements.
        if missing_requirements:
            missing_requirements_dict = dict()
            print(install_parsers)
            for identifier, (parser, path) in install_parsers.items():
                missing = tuple(
                    x for x in parser.requirements if x in missing_requirements
                )
                if missing:
                    missing_requirements_dict[parser.identifier] = missing
            raise RuntimeError(
                "Installation failed. Unsatisfied requirements: \n - %s"
                % "\n - ".join(
                    [f"{n}: {r}" for n, r in missing_requirements_dict.items()]
                )
            )

        if install_parsers:
            logger.info(
                "Will install the following packages: %s."
                % ", ".join(install_parsers)
            )
            logger.info(
                "Will install the following namespaces: %s."
                % ", ".join(
                    name
                    for identifier, (parser, path) in install_parsers.items()
                    for name in parser.namespaces.keys()
                )
            )

            for identifier, (parser, path) in install_parsers.items():
                parser.install(self.path)

            logger.info("Installation successful")

            self._reload_installed_ontologies()

    def uninstall(self, *packages: str) -> None:
        """Uninstall ontology packages.

        Args:
            packages: Identifiers of the ontology packages to uninstall.
        """
        installed_identifiers: Set[str] = set(self._package_names)
        remove_identifiers: Set[str] = set(packages)
        not_installed_identifiers: Set[str] = (
            remove_identifiers - installed_identifiers
        )
        if not_installed_identifiers:
            raise RuntimeError(
                f"Cannot uninstall the following packages, "
                f"as they are not installed: "
                f"{', '.join(not_installed_identifiers)}."
            )

        # Load the installed packages and create a dependency graph. In such
        # a graph, given an arc, the tail is a package and the head a
        # package that depends on it.
        paths = {
            os.path.join(self.path, yml)
            for yml in (
                x
                for x in os.listdir(self.path)
                if "yml" in str(os.path.splitext(x)[1])
            )
        }
        parsers = {OntologyParser.get_parser(path) for path in paths}
        directed_edges = {
            (requirement, parser.identifier)
            for parser in parsers
            for requirement in parser.requirements
        }
        requirements_graph = graph_set_to_dict(directed_edges)
        del directed_edges, parsers, paths

        depth_first_search_iterator = depth_first_search(
            requirements_graph,
            remove_identifiers,
            lambda node: True,
            # Every node reachable from the starting nodes is required to be
            # removed to leave the system in a healthy state.
        )
        should_be_removed = set(depth_first_search_iterator)

        # Block package removal if another package depends on it.
        conflicts = should_be_removed - remove_identifiers
        if conflicts:
            # Create a graph of conflicts from the requirements graph.
            detailed_conflicts = {
                (target, source)
                for source, targets in requirements_graph.items()
                if source in should_be_removed
                for target in targets
                if target in conflicts
            }
            detailed_conflicts = graph_set_to_dict(detailed_conflicts)
            # Filter out tails with no heads.
            detailed_conflicts = {
                key: value
                for key, value in detailed_conflicts.items()
                if value
            }

            message = (
                "Cannot remove package{plural} {cannot_remove}{comma} "
                "because other installed packages depend on {pronoun}: "
                "{dependency_list}. "
                "Please remove the packages {all_packages_to_remove} "
                "all together."
            )
            plural = "s" if len(remove_identifiers) > 1 else ""
            comma = ";" if plural else ","
            pronoun = "them" if plural else "it"
            cannot_remove = ", ".join(remove_identifiers)
            one_dependency = next(iter(detailed_conflicts.values()))
            all_dependencies_equal = all(
                one_dependency == x for x in detailed_conflicts.values()
            )
            if all_dependencies_equal:
                dependency_list = ", ".join(detailed_conflicts)
            else:
                dependency_list = set()
                for package, conflict_list in detailed_conflicts.items():
                    dependency_list.add(
                        f"package {package} depends on "
                        f"{', '.join(conflict_list)}"
                    )
                dependency_list = "; ".join(dependency_list)
            all_packages_to_remove = set(should_be_removed)
            last_package = all_packages_to_remove.pop()
            all_packages_to_remove = (
                ", ".join(all_packages_to_remove) + " and " + last_package
            )
            message = message.format(
                plural=plural,
                cannot_remove=cannot_remove,
                comma=comma,
                pronoun=pronoun,
                dependency_list=dependency_list,
                all_packages_to_remove=all_packages_to_remove,
            )
            raise RuntimeError(message)

        if remove_identifiers:
            files_to_remove = (
                glob.glob(os.path.join(self.path, f"{identifier}*"))
                for identifier in remove_identifiers
            )
            files_to_remove = {
                file for glob_list in files_to_remove for file in glob_list
            }
            for file in files_to_remove:
                os.remove(file)

            logger.info("Uninstallation successful")

            self._reload_installed_ontologies()

    @staticmethod
    def get_default_installation_path() -> Path:
        """Get the path where ontologies are installed by default."""
        # Get the path from the environment variable if defined.
        path = os.environ.get("SIMPHONY_ONTOLOGIES_DIR")
        if path:
            path = Path(path)

        # If the environment variable is not defined, use the default path.
        path = path or Path.home() / ".simphony-osp" / "ontologies"

        return path

    def set_default_installation_path(
        self, value: Optional[Union[str, Path]]
    ) -> None:
        """Set the path where ontologies are installed by default."""
        path = self.path

        if value is not None:
            os.environ["SIMPHONY_ONTOLOGIES_DIR"] = str(value)
        else:
            del os.environ["SIMPHONY_ONTOLOGIES_DIR"]

        if path != self.path:
            self._reload_installed_ontologies()

    _path: Optional[Path] = None
    _ontology: Session

    @property
    def _package_names(self) -> Iterator[str]:
        """Get the names of the installed packages.

        Returns:
            Identifiers of the installed packages.
        """
        return (
            OntologyParser.get_parser(path).identifier
            for path in self._package_paths
        )

    @property
    def _package_paths(self) -> Iterator[Path]:
        """Get the paths of the files describing the installed packages."""
        return (
            Path(self.path) / yml
            for yml in (
                str(x)
                for x in os.listdir(self.path)
                if "yml" in str(os.path.splitext(x)[1])
            )
        )

    @property
    def _package_names_paths(self) -> Iterator[Tuple[str, Path]]:
        """Get both the identifiers and the paths of the installed packages."""
        return (
            (OntologyParser.get_parser(path).identifier, path)
            for path in self._package_paths
        )

    @property
    def _topologically_sorted_parsers(self) -> List[OntologyParser]:
        """Returns a list of parsers, topologically sorted.

        As the parsers are topologically sorted with respect to their
        requirements, they can be loaded in order without triggering missing
        ontology entity errors.
        """
        paths = self._package_paths
        parsers = {OntologyParser.get_parser(path) for path in paths}
        directed_edges = {
            (requirement, parser.identifier)
            for parser in parsers
            for requirement in parser.requirements or (None,)
        }
        graph = graph_set_to_dict(directed_edges)
        sorted_identifiers = topological_sort(graph)
        parsers = sorted(
            parsers, key=lambda x: sorted_identifiers.index(x.identifier)
        )
        return parsers

    def _reload_installed_ontologies(self):
        self._ontology.clear(force=True)
        for parser in self._topologically_sorted_parsers:
            self._ontology.load_parser(parser)


# Create a pico singleton for the default directory and set the installed
# packages as the default ontology.
pico = Pico()
Session.default_ontology = pico.ontology
