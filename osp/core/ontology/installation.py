import os
import logging
import shutil
from osp.core.ontology.parser import Parser

logger = logging.getLogger(__name__)


class OntologyInstallationManager():
    def __init__(self, namespace_registry=None, path=None):
        import osp.core.namespaces as namespaces
        self.namespace_registry = namespace_registry
        self.path = path or namespaces._path
        if self.namespace_registry is None:
            self.namespace_registry = namespaces._namespace_registry

    def install(self, *files):
        self._install(files, self._get_new_packages, False)
        logger.info("Installation successful")

    def uninstall(self, *files_or_namespaces):
        self._install(files_or_namespaces, self._get_remaining_packages, True)
        logger.info("Uninstallation successful")

    def install_overwrite(self, *files):
        self._install(files, self._get_replaced_packages, True)
        logger.info("Installation successful")

    def get_installed_packages(self, return_path=False):
        result = list()
        for item in os.listdir(self.path):
            if item.endswith(".yml"):
                result.append(item.split(".")[0])
                if return_path:
                    result[-1] = (result[-1], os.path.join(self.path, item))
        return result

    def _get_remaining_packages(self, remove_packages):
        remove_pkgs = set()
        installed_pkgs = dict(self.get_installed_packages(return_path=True))
        for pkg in remove_packages:
            if pkg.endswith(".yml") and os.path.exists(pkg):
                pkg = Parser.get_identifier(pkg)
            if pkg in installed_pkgs:
                remove_pkgs.add(pkg)
            else:
                raise ValueError("Could not uninstall %s. No file nor "
                                 "installed ontology package." % pkg)
        return [v for k, v in installed_pkgs.items() if k not in remove_pkgs]

    def _get_replaced_packages(self, new_packages):
        installed = dict(self.get_installed_packages(return_path=True))
        for pkg in new_packages:
            installed[Parser.get_identifier(pkg)] = pkg
        return installed.values()

    def _get_new_packages(self, packages):
        result = set(packages)
        installed = set(self.get_installed_packages())
        for pkg in packages:
            identifier = Parser.get_identifier(pkg)
            if identifier in installed:
                logger.info("Skipping package %s with identifier %s, "
                            "because it is already installed."
                            % (pkg, identifier))
                result.remove(pkg)
        return result

    def _install(self, files, filter_func, clear):
        graph = self.namespace_registry._graph
        if clear:
            graph = self.namespace_registry.clear()
        files = filter_func(files)  # TODO order files
        parser = Parser(graph)
        for file in files:
            parser.parse(file)
        self.namespace_registry.update_namespaces()
        # serialize the result
        if clear:
            shutil.rmtree(self.path)
            os.makedirs(self.path)
        parser.store(self.path)
        self.namespace_registry.store(self.path)
