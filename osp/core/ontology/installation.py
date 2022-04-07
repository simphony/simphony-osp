"""This class handles the installation of ontologies."""

import glob
import logging
import os
import shutil
import sys
import tempfile
from typing import Dict, Set

from osp.core.ontology.parser.parser import OntologyParser

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OntologyInstallationManager:
    """This class handles the installation of ontologies."""

    def __init__(self, namespace_registry=None, path=None):
        """Initialize the installer.

        Args:
            namespace_registry (OntologyNamespaceRegistry, optional): A custom
                namespace registry.. Defaults to None.
            path (str, optional): Installation destination. Defaults to None.
        """
        self.namespace_registry = namespace_registry
        self.path = path
        if self.namespace_registry is None:
            from osp.core.ontology.namespace_registry import namespace_registry

            self.namespace_registry = namespace_registry

    @property
    def path(self) -> str:
        """Path where ontologies are installed."""
        return self._path or self.get_default_installation_path()

    @path.setter
    def path(self, value: str):
        """Set the path where ontologies are installed."""
        self._path = value

    @classmethod
    def get_default_installation_path(cls):
        """Get the path where ontologies are installed by default."""
        osp_ontologies_dir = os.environ.get(
            "OSP_ONTOLOGIES_DIR"
        ) or os.path.expanduser("~")
        return os.path.join(osp_ontologies_dir, ".osp_ontologies")

    @classmethod
    def set_default_installation_path(cls, value: str):
        """Set the path where ontologies are installed by default.

        Note: this has the same effect as setting the environment variable
        `OSP_ONTOLOGIES_DIR`. This means that in fact, the ontologies will
        be installed to `OSP_ONTOLOGIES_DIR/.osp_ontologies` (just look at
        the `get_default_installation_path` method).
        """
        os.environ["OSP_ONTOLOGIES_DIR"] = value

    def install(self, *files):
        """Install given packages. Skip already installed ones."""
        self._install(files, self._get_new_packages, False)
        logger.info("Installation successful")

    def uninstall(self, *files_or_namespaces):
        """Uninstall given packages."""
        self._install(files_or_namespaces, self._get_remaining_packages, True)
        logger.info("Uninstallation successful")

    def install_overwrite(self, *files):
        """Install packages and overwrite already installed ones."""
        self._install(files, self._get_replaced_packages, True)
        logger.info("Installation successful")

    def get_installed_packages(self, return_path=False):
        """Get the list of installed packages.

        Args:
            return_path (bool, optional): Whether to return the path to the
                file, too. Defaults to False.

        Returns:
            Tuple[str]: The installed packages.
        """
        result = list()
        for item in os.listdir(self.path):
            if item.endswith(".yml"):
                result.append(item.split(".")[0])
                if return_path:
                    result[-1] = (result[-1], os.path.join(self.path, item))
        return set(result)

    def _get_remaining_packages(self, remove_packages):
        """Get package paths to install.

        Get list of packages that remain after given list of packages
        have been removed.

        Args:
            remove_packages (List[str]): List of packages to remove.

        Raises:
            ValueError: Given package to remove is not installed

        Returns:
            List[str]: The remaining packages.
        """
        remove_pkgs = set()
        installed_pkgs = dict(self.get_installed_packages(return_path=True))
        for pkg in remove_packages:
            if pkg.endswith(".yml") and os.path.exists(pkg):
                pkg = OntologyParser.get_parser(pkg).identifier
            if pkg in installed_pkgs:
                remove_pkgs.add(pkg)
            else:
                raise ValueError(
                    "Could not uninstall %s. No file nor "
                    "installed ontology package. "
                    "Make sure to only specify valid "
                    "yml files or ontology package names." % pkg
                )

        remaining_packages = {
            k: v for k, v in installed_pkgs.items() if k not in remove_pkgs
        }

        # Block package removal if another package depends on it.
        remaining_packages_requirements = {
            name: OntologyParser.get_parser(path).requirements
            for name, path in remaining_packages.items()
        }
        all_conflicts = self._resolve_dependencies_removal(
            remaining_packages_requirements, dict(), set(remove_pkgs)
        )
        if all_conflicts:
            """Raise an exception."""
            message = (
                "Cannot remove package{plural} {cannot_remove}{comma} "
                "because other installed packages depend on {pronoun}: "
                "{dependency_list}. "
                "Please remove the packages {all_packages_to_remove} "
                "all together."
            )
            cannot_remove = set(
                conflict
                for conflicts in all_conflicts.values()
                for conflict in conflicts
                if conflict in remove_pkgs
            )
            plural = "s" if len(cannot_remove) > 1 else ""
            comma = ";" if plural else ","
            pronoun = "them" if plural else "it"
            cannot_remove = ", ".join(cannot_remove)
            one_dependency = next(iter(all_conflicts.values()))
            all_dependencies_equal = all(
                one_dependency == x for x in all_conflicts.values()
            )
            if all_dependencies_equal:
                dependency_list = ", ".join(all_conflicts)
            else:
                dependency_list = set()
                for package, conflicts in all_conflicts.items():
                    dependency_list.add(
                        f"package {package} depends on "
                        f"{', '.join(conflicts)}"
                    )
                dependency_list = "; ".join(dependency_list)
            all_packages_to_remove = set(all_conflicts) | remove_pkgs
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

        return [v for v in remaining_packages.values()]

    def _resolve_dependencies_removal(
        self,
        remaining_packages_requirements: Dict[str, Set[str]],
        all_conflicts: Dict[str, Set[str]],
        to_remove: Set[str],
    ) -> Dict[str, Set[str]]:
        """Resolve the dependencies when a package is removed.

        Finds out (using recursive calls) all the packages that would need
        to be removed together with the packages that want to be removed in
        order not to leave broken dependencies.

        Args:
            remaining_packages_requirements: The requirements of the
                packages that would remain installed after uninstalling the
                packages specified in `to_remove`.
            all_conflicts: All the conflicts that accumulate as the
                function is called recursively. At the end, a list of all
                the packages that would need to be removed to leave the
                system in a healthy state can be reconstructed from it.
            to_remove: The packages that are to be removed.
        """
        conflicts: Dict[str, Set[str]] = {
            name: requirements & to_remove
            for name, requirements in remaining_packages_requirements.items()
        }
        conflicts = {
            name: conflicts
            for name, conflicts in conflicts.items()
            if conflicts
        }
        all_conflicts.update(conflicts)
        to_remove.update(conflicts)
        remaining_packages_requirements = {
            package: requires
            for package, requires in remaining_packages_requirements.items()
            if package not in to_remove
        }
        if conflicts:
            self._resolve_dependencies_removal(
                remaining_packages_requirements, all_conflicts, to_remove
            )
        return all_conflicts

    def _get_replaced_packages(self, new_packages):
        """Get package paths to install.

        Get the package paths that by replacing the package paths of
        already installed packages with new packages,

        Args:
            new_packages (List[str]): Path to new package files.

        Returns:
            List[str]: Resulting list of package paths.
        """
        installed = dict(self.get_installed_packages(return_path=True))
        for pkg in new_packages:
            installed[OntologyParser.get_parser(pkg).identifier] = pkg
        return installed.values()

    def _get_new_packages(self, packages):
        """From the given list of packages, return the ones that are new.

        Args:
            packages (List[str]): Path to ontology file.

        Returns:
            List[str]: List of package path that are new
        """
        result = set(packages)
        installed = set(self.get_installed_packages())
        for pkg in packages:
            identifier = OntologyParser.get_parser(pkg).identifier
            if identifier in installed:
                logger.info(
                    "Skipping package %s with identifier %s, "
                    "because it is already installed." % (pkg, identifier)
                )
                result.remove(pkg)
        return result

    def _install(self, files, filter_func, clear):
        """Install the ontology.

        Args:
            files (List[str]): The ontology files to install
            filter_func (Callable): Function that takes the list of files
                as input and returns a list of files that need to be installed.
            clear (bool): Whether it is necessary to clear what is already
                installed.
        """
        # Determine whether the namespace names need to be unbound from the
        # `osp.core.namespaces` and `osp.core` modules manually (Python 3.6)
        # or not.
        python_36 = (sys.version_info.major, sys.version_info.minor) <= (3, 6)
        if python_36 and clear:
            from osp.core.ontology.namespace_registry import namespace_registry

            unbound_manually = (
                True
                if self.namespace_registry is namespace_registry
                else False
            )
        else:
            unbound_manually = False

        os.makedirs(self.path, exist_ok=True)
        # Save existing namespace names if namespaces have to be unbound
        # manually. Otherwise, just set the variable
        # to `None` in order to save computation time.
        unbound_manually = (
            set(ns for ns in self.namespace_registry)
            if unbound_manually
            else set()
        )
        if clear:
            self.namespace_registry.clear()
        files = self._sort_for_installation(
            filter_func(files),
            set(self.get_installed_packages()) if not clear else set(),
        )
        installed_packages = set()
        for file in files:
            parser = OntologyParser.get_parser(file)
            self.namespace_registry.load_parser(parser)
            # serialize the result
            parser.install(self.path)
            installed_packages.add(parser.identifier)
        if clear:
            all_ontology_files, files_to_keep = set(), set()
            for ext in ("yml", "xml"):
                all_ontology_files |= set(
                    os.path.basename(x)
                    for x in glob.glob(os.path.join(self.path, f"*.{ext}"))
                )
                files_to_keep |= set(
                    f"{identifier}.{ext}" for identifier in installed_packages
                )
            files_to_remove = all_ontology_files - files_to_keep
            for file in files_to_remove:
                os.remove(os.path.join(self.path, file))
        if python_36:  # Bound and unbound namespaces manually
            from ... import core
            from .. import namespaces

            if unbound_manually:
                unbound_manually = unbound_manually.difference(
                    ns for ns in self.namespace_registry
                )  # Remove the namespaces that are kept installed.
            self.namespace_registry.update_namespaces(
                modules=[core, namespaces], remove=unbound_manually
            )
        self.namespace_registry.store(self.path)

    def _sort_for_installation(self, files, installed):
        """Get the right order to install the files.

        Args:
            files (List[str]): The list of file paths to sort.

        Raises:
            RuntimeError: Unsatisfied requirements after installation.

        Returns:
            List[str]: The sorted list of file paths.
        """
        result = list()
        files = {OntologyParser.get_parser(f).identifier: f for f in files}
        requirements = {
            n: OntologyParser.get_parser(f).requirements
            for n, f in files.items()
        }

        # If the requirements for an ontology package are bundled with
        # OSP-core, try to install them automatically.
        package_and_dependents = dict()
        try:
            package_and_dependents: Dict[
                str, Set[str]
            ] = self._resolve_dependencies_install(files, requirements, dict())
            files.update(
                {
                    OntologyParser.get_parser(f).identifier: f
                    for f in package_and_dependents
                }
            )
            requirements.update(
                {
                    n: OntologyParser.get_parser(f).requirements
                    for n, f in files.items()
                }
            )
        except FileNotFoundError:
            pass

        # order the files
        while requirements:
            add_to_result = list()
            for namespace, req in requirements.items():
                req -= installed | set(result)
                if not req:
                    add_to_result.append(namespace)
            if not add_to_result:
                raise RuntimeError(
                    "Installation failed. Unsatisfied requirements: \n - %s"
                    % "\n - ".join(
                        ["%s: %s" % (n, r) for n, r in requirements.items()]
                    )
                )
            result += add_to_result
            for x in add_to_result:
                del requirements[x]
        dependencies_to_install = set(package_and_dependents) - set(installed)
        if dependencies_to_install:
            logger.info(
                "Also installing dependencies: %s."
                % ", ".join(dependencies_to_install)
            )
        logger.info("Will install the following namespaces: %s" % result)
        return [files[n] for n in result]

    def _resolve_dependencies_install(
        self,
        files: Dict[str, str],
        requirements: Dict[str, Set[str]],
        dependents: Dict[str, Set[str]],
    ) -> Dict[str, Set[str]]:
        """Find and resolve the dependencies of the packages to be installed.

        Automatic resolution of dependencies is only feasible if the
        dependency is bundled with OSP-core.

        Args:
            files: The packages that are going to be installed together with
                their file path.
            requirements: The dependencies for each package that is going to
                be installed.
            dependents: A dictionary with package names and the packages
                that depend on them.
        """
        initial_files = files
        additional_files: Dict[str, str] = dict()
        # The statement below avoids installing the file bundled with
        # OSP-core when the user provides a custom file providing the same
        # package identifier.
        requirements = {
            n: {req for req in requirements_set if req not in initial_files}
            for n, requirements_set in requirements.items()
        }
        new_requirements: Dict[str, Set[str]] = dict()
        for package, requirements_set in requirements.items():
            # Queue the requirements for installation if bundled with
            # OSP-core and not already queued.
            actually_missing_requirements = {
                package
                for package in requirements_set
                if package not in additional_files
            }
            for requirement in actually_missing_requirements:
                try:
                    parser = OntologyParser.get_parser(requirement)
                    additional_files[parser.identifier] = requirement
                    new_requirements.update(
                        {parser.identifier: parser.requirements}
                    )
                except FileNotFoundError:
                    pass

            # Store which packages are requiring the requirements that were
            # queued for installation to show the information on the logs.
            # In addition, the `dependents` dictionary keys are the
            # additional packages to be installed.
            initially_missing_requirements = {
                package
                for package in requirements_set
                if package not in initial_files
            }
            for requirement in initially_missing_requirements:
                dependents[requirement] = dependents.get(
                    requirement, set()
                ) | {package}
        files.update(additional_files)
        new_requirements_exist = bool(
            {req for req_set in new_requirements.values() for req in req_set}
            - {req for req_set in requirements.values() for req in req_set}
        )
        if new_requirements_exist:
            requirements.update(new_requirements)
            dependents = self._resolve_dependencies_install(
                files, requirements, dependents
            )
        return dependents


def pico_migrate(namespace_registry, path):
    """Migrate old installations to new.

    Args:
        namespace_registry (NamespaceRegistry): The namespace registry
        path (str): The installation path
    """
    logger.info("Migrating installed ontologies to new osp-core version.")
    yml_path = os.path.join(path, "yml", "installed")
    with tempfile.TemporaryDirectory() as d:
        files = list()
        for file in os.listdir(yml_path):
            if file == "ontology.cuba.yml" or file == "cuba.ontology.yml":
                continue
            os.rename(os.path.join(yml_path, file), os.path.join(d, file))
            files.append(os.path.join(d, file))
        shutil.rmtree(path)
        os.mkdir(path)
        installer = OntologyInstallationManager(namespace_registry, path)
        namespace_registry._load_cuba()
        installer.install(*files)


def pico_migrate_v3_5_3_1(
    path, migration_version_file, namespace_registry=None
):
    """Migrate old installations to v3.5.3.1.

    The migration function `pico_migrate` should be applied before this one if
    necessary.

    Args:
        path (str): The installation path.
        migration_version_file (str): The path of the file that will contain
            the version of osp-core associated with this migration.
        namespace_registry (OntologyInstallationManager): use a specific
            namespace registry in this migration function.
    """
    logger.info("Migrating installed ontologies to new osp-core version.")
    try:
        os.remove(os.path.join(path, "namespaces.txt"))
    except FileNotFoundError:
        pass
    ontology_installer = OntologyInstallationManager(
        namespace_registry=namespace_registry, path=path
    )
    ontology_installer.uninstall()
    with open(os.path.join(path, migration_version_file), "w") as version_file:
        version_file.write("3.5.3.1" + "\n")
