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

    def get_installed_packages(self):
        result = list()
        for item in os.listdir(self.installed_path):
            if item.endswith(".yml"):
                result.append(item.split(".")[0])
        return result

    def get_remaining_packages(self, remove_packages):
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
        return set(self.get_installed_packages()) - remove_pkgs

    def install(self, *files, success_msg=True):
        """Install the given files with the current namespace registry.

        :param files: The files to install, defaults to None
        :type files: str, optional
        :param success_msg: Whether a logging message should be printed
            if installation succeeds.
        :type success_msg: bool
        """
        # parse the files
        parser = Parser(self.namespace_registry._graph)
        parser.parse(*files, skip_identifiers=self.get_installed_packages())
        self.namespace_registry.update_namespaces()
        # serialize the result
        parser.store(self.installed_path)
        self.namespace_registry.store(self.installed_path)
        if success_msg:
            logger.info("Installation successful!")

    def uninstall(self, *packages, success_msg=True, _force=False):
        """Uninstall the given namespaces

        :param packages: The packages to uninstall
        :type packages: List[str]
        :raises ValueError: The namespace to uninstall is not installed
        :param success_msg: Whether a logging message should be printed
            if uninstallation succeeds.
        :type success_msg: bool
        :param _force: Whether to uninstall even if resulting
            state will be broken.
            WARNING: Can result in broken state of osp-core.
        :type _force: bool
        """
        graph = self.namespace_registry.clear()
        remaining_packages = self.get_remaining_packages(packages)
        parser = Parser(graph)
        parser.parse(*remaining_packages)
        self.namespace_registry.update_namespaces()
        # serialize the result
        shutil.rmtree(self.installed_path)
        os.makedirs(self.installed_path)
        parser.store(self.installed_path)
        self.namespace_registry.store(self.installed_path)
        if success_msg:
            logger.info("Uninstallation successful!")


    # def install_overwrite(self, *files, use_pickle=True):
    #     """Install the given files. Overwrite them if they have been installed already.

    #     :param use_pickle: Whether to pickle for installing, defaults to True
    #     :type use_pickle: bool, optional
    #     """
    #     try:
    #         self._create_rollback_snapshot()
    #         self.uninstall(*map(self._get_namespace, files),
    #                        success_msg=False, _force=True)
    #         try:
    #             self.install(*files, use_pickle=use_pickle)
    #         except Exception:  # unsatisfied requirements
    #             self._rollback(use_pickle)
    #             logger.error("Error during installation.",
    #                          exc_info=1)
    #             logger.error("Installation failed. Rolled back!")
    #     finally:
    #         self._dismiss_rollback_snapshot()

    # def _create_rollback_snapshot(self):
    #     """Create a snapshot of the installed ontologies:
    #     Move the YAML file of all installed ontologies to a temporary directory
    #     """
    #     self._dismiss_rollback_snapshot()
    #     logger.debug("Create snapshot of installed ontologies: %s"
    #                  % os.listdir(self.installed_path))
    #     logger.debug("Copy directory %s to %s"
    #                  % (self.installed_path, self.rollback_path))
    #     copytree(self.installed_path, self.rollback_path)

    # def _dismiss_rollback_snapshot(self):
    #     """Remove the temporary snapshot directory"""
    #     if os.path.exists(self.rollback_path):
    #         rmtree(self.rollback_path)
    #     logger.debug("Dismiss snapshot of installed ontologies!")

    # def _rollback(self, use_pickle=True):
    #     """Dismiss the currently installed ontologies and go
    #     back to the last snapshot.

    #     :param use_pickle: Whether to use pickle for installation,
    #         defaults to True
    #     :type use_pickle: bool, optional
    #     """
    #     if os.path.exists(self.pkl_path):
    #         os.remove(self.pkl_path)
    #     rmtree(self.installed_path)
    #     rmtree(self.tmp_path)
    #     logger.debug("Rollback installed ontologies to last snapshot: %s"
    #                  % os.listdir(self.rollback_path))
    #     logger.debug("Copy directory %s to %s" % (self.rollback_path,
    #                                               self.installed_path))
    #     copytree(self.rollback_path, self.installed_path)
    #     self.initialise_installed_ontologies()
    #     self.install(use_pickle=use_pickle, success_msg=False)

    # @staticmethod
    # def _get_onto_metadata(file_path):
    #     """Get the metadata of the ontology

    #     :param file_path: The path to the yaml ontology file
    #     :type file_path: str
    #     :raises RuntimeError: There is no namespace defined
    #     """

    #     # Get the namespace
    #     file_path = Parser.get_filepath(file_path)
    #     lines = ""
    #     with open(file_path, "r") as f:
    #         for line in f:
    #             lines += line
    #             line = line.strip().lower()
    #             if line.startswith(ONTOLOGY_KEY):
    #                 break
    #     return yaml.safe_load(lines)

    # @staticmethod
    # def _get_namespace(file_path):
    #     """Get the namespace of the ontology

    #     :param file_path: The path to the yaml ontology file
    #     :type file_path: str
    #     :raises RuntimeError: There is no namespace defined
    #     """
    #     yaml_doc = OntologyInstallationManager._get_onto_metadata(file_path)
    #     return yaml_doc[NAMESPACE_KEY].lower()

    # @staticmethod
    # def get_requirements(file_path):
    #     """Get the requirements of a yml file

    #     :param file_path: The path to the yaml ontology file
    #     :type file_path: str
    #     """
    #     yaml_doc = OntologyInstallationManager._get_onto_metadata(file_path)
    #     try:
    #         req = set(map(str.lower, yaml_doc[REQUIREMENTS_KEY])) | {"cuba"}
    #         logger.debug("%s has the following requirements: %s"
    #                      % (file_path, req))
    #         return req
    #     except KeyError:
    #         return set(["cuba"])

    # def set_module_attr(self, module=None):
    #     if module is None:
    #         import osp.core as module
    #     setattr(module, "ONTOLOGY_NAMESPACE_REGISTRY",
    #             self.namespace_registry)
    #     for name, namespace in self.namespace_registry._namespaces.items():
    #         setattr(module, name.upper(), namespace)
    #         setattr(module, name.lower(), namespace)
