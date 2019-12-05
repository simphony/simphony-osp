import os
import argparse
import uuid
import pickle  # nosec
from shutil import copyfile
import osp.core
from osp.core.ontology.parser import Parser
from osp.core.ontology.namespace_registry import NamespaceRegistry


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
            copyfile(file_path, os.path.join(self.tmp_path, filename))

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
        files = self._sort_for_installation(files)
        for file in files:
            self.parser.parse(file, osp_module=osp_module)

    def install(self, *files, use_pickle=True):
        """Install the given files with the current namespace registry.

        :param files: The files to install, defaults to None
        :type files: str, optional
        :param use_pickle: Whether to pickle for installing, defaults to True
        :type use_pickle: bool, optional
        """
        # parse the files
        if files:
            self.parse_files(files)

        # move the files
        for file in os.listdir(self.tmp_path):
            os.replace(os.path.join(self.tmp_path, file),
                       os.path.join(self.installed_path, file))

        # create the pickle file
        if os.path.exists(self.pkl_path):
            os.remove(self.pkl_path)
        if use_pickle:
            with open(self.pkl_path, "wb") as f:
                pickle.dump(self.namespace_registry, f)
        self.set_module_attr()

    def uninstall(self, *namespaces):
        """Uninstall the given namespaces

        :param namespaces: The namespaces to uninstall
        :type namespaces: List[str]
        :raises ValueError: The namespace to uninstall is not installed
        """
        # Remove the yaml files
        for namespace in namespaces:
            namespace = namespace.lower()
            p = os.path.join(self.installed_path,
                             "ontology.%s.yml" % namespace)
            if os.path.exists(p):
                os.remove(p)
                delattr(osp.core, namespace.upper())
                delattr(osp.core, namespace.lower())
            else:
                raise ValueError("Namespace %s not installed" % namespace)

        # remove the pickle file
        pkl_exists = os.path.exists(self.pkl_path)
        if pkl_exists:
            os.remove(self.pkl_path)

        # reinstall remaining namespaces
        self.initialize_installed_ontologies()
        self.install(use_pickle=pkl_exists)

    def initialize_installed_ontologies(self, osp_module=None,
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

    def _sort_for_installation(self, files):
        """Get the right order to install the files.

        :param files: The list of file paths to sort.
        :type files: List[str]
        :return: The sorted list of file paths.
        :rtype: List[str]
        """
        namespaces = [self._get_namespace(f) for f in files]
        if "cuba" in namespaces:
            cuba_idx = namespaces.index("cuba")
            files = files[cuba_idx: cuba_idx + 1] + files[:cuba_idx] + \
                files[cuba_idx + 1:]
            namespaces = namespaces[cuba_idx: cuba_idx + 1] + \
                namespaces[:cuba_idx] + namespaces[cuba_idx + 1:]
        else:
            namespaces = ["cuba"] + namespaces
            files = ["cuba"] + list(files)

        result = list()
        for file, namespace in zip(files, namespaces):
            if namespace not in self.namespace_registry:
                result.append(file)
        return result

    @staticmethod
    def _get_namespace(file_path):
        """Get the namespace of a file

        :param file_path: The path to the yaml ontology file
        :type file_path: str
        :raises RuntimeError: There is no namespace defined
        """

        # Get the namespace
        namespace = None
        file_path = Parser.get_filepath(file_path)
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith("namespace"):
                    namespace = line.split(":")[1].strip().strip("\"'")
        if namespace is None:
            raise RuntimeError("The file %s is missing a namespace"
                               % file_path)
        return namespace.lower()

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

    args = parser.parse_args()

    from osp.core import ONTOLOGY_INSTALLER
    if args.command == "install":
        ONTOLOGY_INSTALLER.install(*args.files, use_pickle=args.pickle)
    elif args.command == "uninstall":
        ONTOLOGY_INSTALLER.uninstall(*args.namespaces)


if __name__ == "__main__":
    install_from_terminal()
