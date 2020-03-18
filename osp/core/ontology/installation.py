import os
import argparse
import uuid
import pickle  # nosec
import yaml
import logging
import subprocess
from shutil import copyfile, rmtree, copytree
import osp.core
from osp.core.ontology.parser import Parser
from osp.core.ontology.keywords import (
    ONTOLOGY_KEY, NAMESPACE_KEY, REQUIREMENTS_KEY
)
from osp.core.ontology.namespace_registry import NamespaceRegistry

logger = logging.getLogger(__name__)


class OntologyInstallationManager():
    def __init__(self, path=None):
        self.namespace_registry = None
        self.parser = None
        self.session_id = uuid.uuid4()
        self.path = os.path.join(
            path or os.path.expanduser("~"),
            ".osp_ontologies")
        self.yaml_path = os.path.join(self.path, "yml")
        self.installed_path = os.path.join(self.yaml_path, "installed")
        self.tmp_path = os.path.join(self.yaml_path, str(self.session_id))
        self.pkl_path = os.path.join(self.path, "ontology.pkl")
        self.rollback_path = os.path.join(self.yaml_path, "rollback")

    def tmp_open(self, file_path):
        """Copy the yaml file to the temporary folder.

        :param file_path: The file to move to the tmp folder
        :type file_path: str
        :raises RuntimeError: No namespace defined in file.
        """
        namespace = self._get_namespace(file_path)

        # copy the file
        filename = "ontology.%s.yml" % namespace
        if not os.path.exists(os.path.join(self.installed_path, filename)):
            dest = os.path.join(self.tmp_path, filename)
            logger.debug("Copy file %s to %s" % (file_path, dest))
            copyfile(file_path, dest)

    def _clean(self):
        """Remove the temporary files."""
        # remove the files in the session
        for file in os.listdir(self.tmp_path):
            file = os.path.join(self.tmp_path, file)
            os.remove(file)
        os.rmdir(self.tmp_path)

    def parse_files(self, files, osp_module=None):
        """Parse multiple files. Will install them in the right order.

        :param files: The files to parse
        :type files: List[str]
        """
        result = list()
        files = self._sort_for_installation(files)
        for file in files:
            n = self.parser.parse(file, osp_module=osp_module)
            result.append(n)
        return result

    def install(self, *files, use_pickle=True, success_msg=True):
        """Install the given files with the current namespace registry.

        :param files: The files to install, defaults to None
        :type files: str, optional
        :param use_pickle: Whether to pickle for installing, defaults to True
        :type use_pickle: bool, optional
        :param success_msg: Whether a logging message should be printed
            if installation succeeds.
        :type success_msg: bool
        """
        # parse the files
        owl_files = {f for f in files
                     if f.endswith(".owl") or f.endswith(".rdf")}
        java_base = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", "java")
        )
        cmd = [
            "java", "-cp",
            java_base + "/target/osp.core-3.4.4-beta.jar:"
            + java_base + "/lib/jars/*",
            "-Djava.library.path="
            + java_base + "/lib/so", "org.simphony.OntologyLoader"
        ] + list(owl_files)
        logger.info("Running Reasoner")
        logger.debug(" ".join(cmd))
        subprocess.run(cmd)
        files = [f for f in files if f not in owl_files]
        if files:
            self.parse_files(files)

        # move the files
        for file in os.listdir(self.tmp_path):
            orig = os.path.join(self.tmp_path, file)
            dest = os.path.join(self.installed_path, file)
            logger.debug("Move directory %s to %s" % (orig, dest))
            os.replace(orig, dest)

        # create the pickle file
        if os.path.exists(self.pkl_path):
            os.remove(self.pkl_path)
        if use_pickle:
            with open(self.pkl_path, "wb") as f:
                pickle.dump(self.namespace_registry, f)
        self.set_module_attr()
        if success_msg:
            logger.info("Installation successful!")

    def uninstall(self, *namespaces, success_msg=True, _force=False):
        """Uninstall the given namespaces

        :param namespaces: The namespaces to uninstall
        :type namespaces: List[str]
        :raises ValueError: The namespace to uninstall is not installed
        :param success_msg: Whether a logging message should be printed
            if uninstallation succeeds.
        :type success_msg: bool
        :param _force: Whether to uninstall even if resulting
            state will be broken.
            WARNING: Can result in broken state of osp-core.
        :type _force: bool
        """
        try:
            if not _force:
                self._create_rollback_snapshot()
            for namespace in namespaces:
                if namespace.endswith("yml") and os.path.exists(namespace):
                    file = namespace
                    namespace = self._get_onto_metadata(file)[NAMESPACE_KEY]
                    logger.info("File %s provided for uninstallation. "
                                % (file))
                logger.info("Uninstalling namespace %s." % namespace)
                namespace = namespace.lower()
                filename = "ontology.%s.yml" % namespace
                path = os.path.join(self.installed_path, filename)
                if os.path.exists(path):
                    os.remove(path)

                    # Remove the attributes of the osp.core package
                    if hasattr(osp.core, namespace.upper()):
                        delattr(osp.core, namespace.upper())
                    if hasattr(osp.core, namespace.lower()):
                        delattr(osp.core, namespace.lower())
                elif _force:
                    continue
                else:
                    raise ValueError("Namespace %s not installed" % namespace)

            # remove the pickle file
            pkl_exists = os.path.exists(self.pkl_path)
            if pkl_exists:
                os.remove(self.pkl_path)

            try:
                # reinstall remaining namespaces
                self.initialise_installed_ontologies()
                self.install(use_pickle=pkl_exists, success_msg=False)
                if success_msg:
                    logger.info("Uninstallation successful!")
            except RuntimeError:  # unsatisfied requirements
                if _force:
                    logger.debug("Temporarily broken state.", exc_info=True)
                    return
                self._rollback(pkl_exists)
                logger.error("Unsatisfied requirements after uninstallation.",
                             exc_info=1)
                logger.error("Uninstallation failed. Rolled back!")
        finally:
            if not _force:
                self._dismiss_rollback_snapshot()

    def install_overwrite(self, *files, use_pickle=True):
        """Install the given files. Overwrite them if they have been installed already.

        :param use_pickle: Whether to pickle for installing, defaults to True
        :type use_pickle: bool, optional
        """
        try:
            self._create_rollback_snapshot()
            self.uninstall(*map(self._get_namespace, files),
                           success_msg=False, _force=True)
            try:
                self.install(*files, use_pickle=use_pickle)
            except Exception:  # unsatisfied requirements
                self._rollback(use_pickle)
                logger.error("Error during installation.",
                             exc_info=1)
                logger.error("Installation failed. Rolled back!")
        finally:
            self._dismiss_rollback_snapshot()

    def initialise_installed_ontologies(self, osp_module=None,
                                        use_pickle=True):
        """Load the installed ontologies.

        :param use_pickle: Whether to use the provided pickle file,
            defaults to True
        :type use_pickle: bool, optional
        """
        self._create_directories()

        # Load pickle
        self.namespace_registry = None
        self.parser = None
        if os.path.exists(self.pkl_path) and use_pickle:
            try:
                with open(self.pkl_path, "rb") as f:
                    self.namespace_registry = pickle.load(f)  # nosec
                    self.parser = Parser(self)
                    self.set_module_attr(osp_module)
                    return
            except EOFError:
                pass

        # Load yaml files
        self.namespace_registry = NamespaceRegistry()
        self.parser = Parser(self)
        installed_files = [os.path.join(self.installed_path, file)
                           for file in os.listdir(self.installed_path)]
        self.parse_files(installed_files or list(), osp_module=osp_module)

    def _create_directories(self):
        """Create the necessary directories if they don't exist."""
        for p in [self.path, self.yaml_path,
                  self.installed_path, self.tmp_path]:
            if not os.path.exists(p):
                os.mkdir(p)

    def _create_rollback_snapshot(self):
        """Create a snapshot of the installed ontologies:
        Move the YAML file of all installed ontologies to a temporary directory
        """
        self._dismiss_rollback_snapshot()
        logger.debug("Create snapshot of installed ontologies: %s"
                     % os.listdir(self.installed_path))
        logger.debug("Copy directory %s to %s"
                     % (self.installed_path, self.rollback_path))
        copytree(self.installed_path, self.rollback_path)

    def _dismiss_rollback_snapshot(self):
        """Remove the temporary snapshot directory"""
        if os.path.exists(self.rollback_path):
            rmtree(self.rollback_path)
        logger.debug("Dismiss snapshot of installed ontologies!")

    def _rollback(self, use_pickle=True):
        """Dismiss the currently installed ontologies and go
        back to the last snapshot.

        :param use_pickle: Whether to use pickle for installation,
            defaults to True
        :type use_pickle: bool, optional
        """
        if os.path.exists(self.pkl_path):
            os.remove(self.pkl_path)
        rmtree(self.installed_path)
        rmtree(self.tmp_path)
        logger.debug("Rollback installed ontologies to last snapshot: %s"
                     % os.listdir(self.rollback_path))
        logger.debug("Copy directory %s to %s" % (self.rollback_path,
                                                  self.installed_path))
        copytree(self.rollback_path, self.installed_path)
        self.initialise_installed_ontologies()
        self.install(use_pickle=use_pickle, success_msg=False)

    def _sort_for_installation(self, files):
        """Get the right order to install the files.

        :param files: The list of file paths to sort.
        :type files: List[str]
        :return: The sorted list of file paths.
        :rtype: List[str]
        """
        result = list()
        files = {self._get_namespace(f): f for f in files}
        requirements = {n: self.get_requirements(f) for n, f in files.items()}
        if "cuba" not in self.namespace_registry:
            if "cuba" not in files:
                files["cuba"] = "cuba"
            requirements["cuba"] = set()

        # Check what has been already installed
        already_installed = list()
        for namespace, file in files.items():
            if namespace in self.namespace_registry:
                logger.warning("Skipping %s. Namespace %s already installed!",
                               file, namespace)
                already_installed.append(namespace)
        for x in already_installed:
            del requirements[x]

        # order the files
        while requirements:
            add_to_result = list()
            for namespace, req in requirements.items():
                req -= set([r for r in req if r in self.namespace_registry])
                req -= set(result)
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

    @staticmethod
    def _get_onto_metadata(file_path):
        """Get the metadata of the ontology

        :param file_path: The path to the yaml ontology file
        :type file_path: str
        :raises RuntimeError: There is no namespace defined
        """

        # Get the namespace
        file_path = Parser.get_filepath(file_path)
        lines = ""
        with open(file_path, "r") as f:
            for line in f:
                lines += line
                line = line.strip().lower()
                if line.startswith(ONTOLOGY_KEY):
                    break
        return yaml.safe_load(lines)

    @staticmethod
    def _get_namespace(file_path):
        """Get the namespace of the ontology

        :param file_path: The path to the yaml ontology file
        :type file_path: str
        :raises RuntimeError: There is no namespace defined
        """
        yaml_doc = OntologyInstallationManager._get_onto_metadata(file_path)
        return yaml_doc[NAMESPACE_KEY].lower()

    @staticmethod
    def get_requirements(file_path):
        """Get the requirements of a yml file

        :param file_path: The path to the yaml ontology file
        :type file_path: str
        """
        yaml_doc = OntologyInstallationManager._get_onto_metadata(file_path)
        try:
            req = set(map(str.lower, yaml_doc[REQUIREMENTS_KEY])) | {"cuba"}
            logger.debug("%s has the following requirements: %s"
                         % (file_path, req))
            return req
        except KeyError:
            return set(["cuba"])

    def set_module_attr(self, module=None):
        if module is None:
            import osp.core as module
        setattr(module, "ONTOLOGY_NAMESPACE_REGISTRY",
                self.namespace_registry)
        for name, namespace in self.namespace_registry._namespaces.items():
            setattr(module, name.upper(), namespace)
            setattr(module, name.lower(), namespace)


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
        "--no-pickle", dest="pickle", action="store_false",
        help="Do not store parsed ontology in a pickle file for faster import"
    )
    install_parser.add_argument(
        "--pickle", dest="pickle", action="store_true",
        help="Store parsed ontology in a pickle file for faster import"
    )
    install_parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite the existing namespaces, if they are already installed"
    )
    install_parser.set_defaults(pickle=True)

    # uninstall parser
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall ontology namespaces."
    )
    uninstall_parser.add_argument(
        "namespaces", nargs="+", type=str,
        help="List of namespaces to uninstall"
    )
    uninstall_parser.set_defaults(pickle=True)

    # list parser
    subparsers.add_parser(
        "list",
        help="List all installed ontologies."
    )

    args = parser.parse_args()
    logging.getLogger("osp.core").setLevel(getattr(logging, args.log_level))

    from osp.core import ONTOLOGY_INSTALLER

    try:
        all_namespaces = map(lambda x: x.name,
                             ONTOLOGY_INSTALLER.namespace_registry)
        if args.command == "install" and args.overwrite:
            ONTOLOGY_INSTALLER.install_overwrite(*args.files,
                                                 use_pickle=args.pickle)
        elif args.command == "install":
            ONTOLOGY_INSTALLER.install(*args.files, use_pickle=args.pickle)
        elif args.command == "uninstall":
            if args.namespaces == ["*"]:
                args.namespaces = all_namespaces
            ONTOLOGY_INSTALLER.uninstall(*args.namespaces)
        elif args.command == "list":
            print("\n".join(all_namespaces))
    except Exception:
        logger.error("An Exception occurred during installation.", exc_info=1)
        if args.log_level != "DEBUG":
            logger.error("Consider running 'pico --log-level debug %s ...'"
                         % args.command)


if __name__ == "__main__":
    install_from_terminal()
