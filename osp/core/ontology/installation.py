"""This class handles the installation of ontologies."""

import os
import glob
import logging
import shutil
import tempfile
from osp.core.ontology.parser.parser import OntologyParser

logger = logging.getLogger(__name__)


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
        if self.path is None:
            import osp.core.namespaces as namespaces
            self.path = namespaces._path
        if self.namespace_registry is None:
            import osp.core.namespaces as namespaces
            self.namespace_registry = namespaces._namespace_registry

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
                raise ValueError("Could not uninstall %s. No file nor "
                                 "installed ontology package. "
                                 "Make sure to only specify valid "
                                 "yml files or ontology package names." % pkg)
        return [v for k, v in installed_pkgs.items() if k not in remove_pkgs]

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
                logger.info("Skipping package %s with identifier %s, "
                            "because it is already installed."
                            % (pkg, identifier))
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
        os.makedirs(self.path, exist_ok=True)
        if clear:
            self.namespace_registry.clear()
        files = self._sort_for_installation(filter_func(files),
                                            set(self.get_installed_packages())
                                            if not clear else set())
        installed_packages = set()
        for file in files:
            parser = OntologyParser.get_parser(file)
            self.namespace_registry.load_parser(parser)
            # serialize the result
            parser.install(self.path)
            installed_packages.add(parser.identifier)
        if clear:
            all_ontology_files, files_to_keep = set(), set()
            for ext in ('yml', 'xml'):
                all_ontology_files |= set(os.path.basename(x) for x in
                                          glob.glob(
                                              os.path.join(self.path,
                                                           f'*.{ext}')))
                files_to_keep |= set(f'{identifier}.{ext}' for identifier in
                                     installed_packages)
            files_to_remove = all_ontology_files - files_to_keep
            for file in files_to_remove:
                os.remove(os.path.join(self.path, file))
        self.namespace_registry.update_namespaces()
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
        requirements = {n: OntologyParser.get_parser(f).requirements for
                        n, f in files.items()}

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
                    % "\n - ".join(["%s: %s" % (n, r)
                                    for n, r in requirements.items()])
                )
            result += add_to_result
            for x in add_to_result:
                del requirements[x]
        logger.info("Will install the following namespaces: %s"
                    % result)
        return [files[n] for n in result]


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


def pico_migrate_v3_5_3_1(path, migration_version_file,
                          namespace_registry=None):
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
        os.remove(os.path.join(path, 'namespaces.txt'))
    except FileNotFoundError:
        pass
    ontology_installer = OntologyInstallationManager(
        namespace_registry=namespace_registry, path=path)
    ontology_installer.uninstall()
    with open(os.path.join(path, migration_version_file), "w") as version_file:
        version_file.write("3.5.3.1" + '\n')
