import os
import logging
import osp.core.namespaces as namespaces
import yaml
import shutil
from osp.core.owl_ontology.owl_parser import Parser, IDENTIFIER_KEY

logger = logging.getLogger(__name__)


class OntologyInstallationManager():
    def __init__(self, namespace_registry=None, path=None):
        self.namespace_registry = namespace_registry
        if self.namespace_registry is None:
            self.namespace_registry = namespaces._namespace_registry

        if path is None:
            self.main_path = namespaces._path
            self.installed_path = namespaces._installed_path
        else:
            self.main_path = path
            self.installed_path = os.path.join(self.main_path, "installed")
        self.rollback_path = os.path.join(self.main_path, "rollback")

    def install(self, *files):
        self._install(files, self._get_new_packages, False)
        logger.info("Installation successful")

    def uninstall(self, *files_or_namespaces):
        self._install(files_or_namespaces, self._get_remaining_packages, True)
        logger.info("Installation successful")

    def install_overwrite(self, *files):
        self._install(files, self._get_replaced_packages, True)
        logger.info("Installation successful")

    def get_installed_packages(self, return_path=False):
        result = list()
        for item in os.listdir(self.installed_path):
            if item.endswith(".yml"):
                result.append(item.split(".")[0])
                if return_path:
                    result[-1] = (result[-1], item)
        return result

    def _get_remaining_packages(self, remove_packages):
        remove_pkgs = set()
        for pkg in remove_packages:
            if not pkg.endswith(".yml"):
                remove_pkgs.add(pkg)
            elif os.path.exists(pkg):
                with open(pkg, "r") as f:
                    remove_pkgs.add(yaml.safe_load(f)[IDENTIFIER_KEY])
            else:
                raise ValueError("Could not uninstall %s. No file nor "
                                 "installed ontology package." % pkg)
        installed_pkgs = self.get_installed_packages(return_path=True)
        return [v for k, v in installed_pkgs if k not in remove_pkgs]

    def _get_replaced_packages(self, new_packages):
        installed = dict(self.get_installed_packages(return_path=True))
        for pkg in new_packages:
            with open(pkg, "r") as f:
                installed[yaml.safe_load(f)[IDENTIFIER_KEY]] = pkg
        return installed.values()

    def _get_new_packages(self, packages):
        result = set(packages)
        installed = set(self.get_installed_packages())
        for pkg in packages:
            with open(pkg, "r") as f:
                identifier = yaml.safe_load(f)[IDENTIFIER_KEY]
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
        files = filter_func(files)
        parser = Parser(graph)
        parser.parse(*files)
        self.namespace_registry.update_namespaces()
        # serialize the result
        if clear:
            shutil.rmtree(self.installed_path)
            os.makedirs(self.installed_path)
        parser.store(self.installed_path)
        self.namespace_registry.store(self.installed_path)
