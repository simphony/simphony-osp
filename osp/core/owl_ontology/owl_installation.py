import os
import argparse
import logging
import osp.core.namespaces as namespaces
from osp.core.owl_ontology.owl_parser import Parser

logger = logging.getLogger(__name__)


class OntologyInstallationManager():
    def __init__(self, namespace_registry=None, path=None):
        self.namespace_registry = namespace_registry
        if self.namespace_registry is None:
            self.namespace_registry = namespaces._namespace_registry

        if path is None:
            self.main_path = namespaces._owl_initializer.path
            self.installed_path = namespaces._owl_initializer.installed_path
        else:
            self.main_path = path
            self.installed_path = os.path.join(self.main_path, "installed")
        self.rollback_path = os.path.join(self.main_path, "rollback")

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
        parser.parse(*files)
        self.namespace_registry.update_namespaces()
        # serialize the result
        parser.store(self.installed_path)
        self.namespace_registry.store(self.installed_path)
        if success_msg:
            logger.info("Installation successful!")


    # def uninstall(self, *namespaces, success_msg=True, _force=False):
    #     """Uninstall the given namespaces

    #     :param namespaces: The namespaces to uninstall
    #     :type namespaces: List[str]
    #     :raises ValueError: The namespace to uninstall is not installed
    #     :param success_msg: Whether a logging message should be printed
    #         if uninstallation succeeds.
    #     :type success_msg: bool
    #     :param _force: Whether to uninstall even if resulting
    #         state will be broken.
    #         WARNING: Can result in broken state of osp-core.
    #     :type _force: bool
    #     """
    #     try:
    #         if not _force:
    #             self._create_rollback_snapshot()
    #         for namespace in namespaces:
    #             if namespace.endswith("yml") and os.path.exists(namespace):
    #                 file = namespace
    #                 namespace = self._get_onto_metadata(file)[NAMESPACE_KEY]
    #                 logger.info("File %s provided for uninstallation. "
    #                             % (file))
    #             logger.info("Uninstalling namespace %s." % namespace)
    #             namespace = namespace.lower()
    #             filename = "ontology.%s.yml" % namespace
    #             path = os.path.join(self.installed_path, filename)
    #             if os.path.exists(path):
    #                 os.remove(path)

    #                 # Remove the attributes of the osp.core package
    #                 if hasattr(osp.core, namespace.upper()):
    #                     delattr(osp.core, namespace.upper())
    #                 if hasattr(osp.core, namespace.lower()):
    #                     delattr(osp.core, namespace.lower())
    #             elif _force:
    #                 continue
    #             else:
    #                 raise ValueError("Namespace %s not installed" % namespace)

    #         # remove the pickle file
    #         pkl_exists = os.path.exists(self.pkl_path)
    #         if pkl_exists:
    #             os.remove(self.pkl_path)

    #         try:
    #             # reinstall remaining namespaces
    #             self.initialise_installed_ontologies()
    #             self.install(use_pickle=pkl_exists, success_msg=False)
    #             if success_msg:
    #                 logger.info("Uninstallation successful!")
    #         except RuntimeError:  # unsatisfied requirements
    #             if _force:
    #                 logger.debug("Temporarily broken state.", exc_info=True)
    #                 return
    #             self._rollback(pkl_exists)
    #             logger.error("Unsatisfied requirements after uninstallation.",
    #                          exc_info=1)
    #             logger.error("Uninstallation failed. Rolled back!")
    #     finally:
    #         if not _force:
    #             self._dismiss_rollback_snapshot()

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


def install_from_terminal():
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
        help="Install ontology namespaces."
    )
    install_parser.add_argument(
        "files", nargs="+", type=str, help="List of yaml files to install"
    )
    install_parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite the existing namespaces, if they are already installed"
    )

    # uninstall parser
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall ontology namespaces."
    )
    uninstall_parser.add_argument(
        "namespaces", nargs="+", type=str,
        help="List of namespaces to uninstall"
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
        all_namespaces = map(lambda x: x.name,
                             ontology_installer.namespace_registry)
        if args.command == "install" and args.overwrite:
            ontology_installer.install_overwrite(*args.files)
        elif args.command == "install":
            ontology_installer.install(*args.files)
        elif args.command == "uninstall":
            if args.namespaces == ["*"]:
                args.namespaces = all_namespaces
            ontology_installer.uninstall(*args.namespaces)
        elif args.command == "list":
            print("\n".join(all_namespaces))
    except Exception:
        logger.error("An Exception occurred during installation.", exc_info=1)
        if args.log_level != "DEBUG":
            logger.error("Consider running 'pico --log-level debug %s ...'"
                         % args.command)


if __name__ == "__main__":
    install_from_terminal()
