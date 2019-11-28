import os
import argparse
import uuid


def OntologyInstallationManager():
    def __init__(self, namespace_registry, path=None):
        self.namespace_registry = namespace_registry
        self.session_id = uuid.uuid4()
        self.path = path or os.path.join(os.path.expanduser("~"),
                                         ".osp_ontologies")
        self.yaml_path = os.path.join(self.path, "yml")
        self.installed_path = os.path.join(self.yaml_path, "installed")
        self.tmp_path = os.path.join(self.yaml_path, str(self.session_id))

    def tmp_open(self, file):
        pass

    def clean(self):
        pass

    def install(self, files, pickle=True):
        files = self._sort_for_installation(files)
        for file in files:
            self.namespace_registry.parse(file)
        

    def uninstall(self, files):
        pass

    def load(self):
        for p in [self.path, self.yaml_path,
                  self.installed_path, self.tmp_path]:
            if not os.path.exists(p):
                os.mkdir(p)

        self.installed_files = []
        installed_files_path = os.path.join(self.path,
                                            "installed_ontologies")
        if os.path.exists(installed_files_path):
            with open(installed_files_path, "r") as f:
                self.installed_files = [l.strip().split("=") for l in f]

    def _sort_for_installation(self, files):
        return files


def install_from_terminal():
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Install your own ontologies."
    )
    parser.add_argument("command", choices=["install", "uninstall"],
                        help="What do you want to do?")
    parser.add_argument("files", nargs="+", type=str,
                        help="List of yaml files to install")
    parser.add_argument("--no-pickle", dest="pickle", action="store_false",
                        help="Do not store parsed ontology in a pickle "
                        "file for faster import")
    parser.add_argument("--pickle", dest="pickle", action="store_true",
                        help="Store parsed ontology in a pickle "
                        "file for faster import")
    parser.set_defaults(pickle=True)
    args = parser.parse_args()

    installer = OntologyInstallationManager()
    if parser.command == "install":
        installer.install(args.files, pickle=args.pickle)
    if parser.command == "uninstall":
        installer.uninstall(args.files)
