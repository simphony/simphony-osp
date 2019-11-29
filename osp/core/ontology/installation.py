import os
import argparse
import uuid
import pickle  # nosec
from shutil import copyfile
from osp.core.ontology.parser import Parser
from osp.core.ontology.namespace_registry import NamespaceRegistry


class OntologyInstallationManager():
    def __init__(self, path=None):
        self.namespace_registry = None
        self.parser = None
        self.session_id = uuid.uuid4()
        self.path = path or os.path.join(os.path.expanduser("~"),
                                         ".osp_ontologies")
        self.yaml_path = os.path.join(self.path, "yml")
        self.installed_path = os.path.join(self.yaml_path, "installed")
        self.tmp_path = os.path.join(self.yaml_path, str(self.session_id))
        self.pkl_path = os.path.join(self.path, "ontology.pkl")

    def tmp_open(self, file_path):
        # move the files in the temporary folder
        namespace = None
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith("namespace"):
                    namespace = line.split(":")[1].strip().strip("\"'")
        if namespace is None:
            raise RuntimeError("The file %s is missing a namespace"
                               % file_path)
        copyfile(
            file_path, os.path.join(self.tmp_path,
                                    "ontology.%s.yml" % namespace)
        )

    def _clean(self):
        # remove the files in the session
        for file in os.listdir(self.tmp_path):
            file = os.path.join(self.tmp_path, file)
            os.remove(file)
        os.rmdir(self.tmp_path)

    def parse_files(self, files):
        files = self._sort_for_installation(files)
        for file in files:
            self.parser.parse(file)

    def install(self, files=None, do_pickle=True):
        # parse the files
        if files:
            self.parse_files(files)

        # move the files
        for file in os.listdir(self.tmp_path):
            copyfile(os.path.join(self.tmp_path, file),
                     os.path.join(self.installed_path, file))

        # create the pickle file
        if os.path.exists(self.pkl_path):
            os.remove(self.pkl_path)
        if do_pickle:
            with open(self.pkl_path, "wb") as f:
                pickle.dump(self.namespace_registry, f)

    def uninstall(self, namespaces):
        # Remove the yaml files
        for namespace in namespaces:
            namespace = namespace.lower()
            p = os.path.join(self.installed_path,
                             "ontology.%s.yml" % namespace)
            p2 = os.path.join(self.tmp_path,
                              "ontology.%s.yml" % namespace)
            if os.path.exists(p):
                os.remove(p)
                os.remove(p2)
            else:
                raise ValueError("Namespace %s not installed" % namespace)

        # remove the pickle file
        pkl_exists = os.path.exists(self.pkl_path)
        if pkl_exists:
            os.remove(self.pkl_path)

        # reinstall remaining namespaces
        self.initialize_installed_ontologies()
        self.install(do_pickle=pkl_exists)

    def initialize_installed_ontologies(self, use_pickle=True):
        # Create necessary directories
        for p in [self.path, self.yaml_path,
                  self.installed_path, self.tmp_path]:
            if not os.path.exists(p):
                os.mkdir(p)

        # Load pickle
        self.namespace_registry = None
        self.parser = None
        if os.path.exists(self.pkl_path) and use_pickle:
            try:
                with open(self.pkl_path, "rb") as f:
                    self.namespace_registry = pickle.load(f)  # nosec
                    self.parser = Parser(self)
                    return
            except EOFError:
                pass

        # Load yaml files
        self.namespace_registry = NamespaceRegistry()
        self.parser = Parser(self)
        installed_files = [os.path.join(self.installed_path, file)
                           for file in os.listdir(self.installed_path)]
        self.parse_files(installed_files or list())

    def _sort_for_installation(self, files):
        return ["cuba"] + [f for f in files  # TODO parse requirements
                           if f != "cuba"
                           and not f.endswith("ontology.cuba.yml")]


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
        ONTOLOGY_INSTALLER.install(args.files, do_pickle=args.pickle)
    if args.command == "uninstall":
        ONTOLOGY_INSTALLER.uninstall(args.namespaces)
