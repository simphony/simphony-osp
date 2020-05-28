import os
import logging
import shutil
from osp.core.owl_ontology.owl_parser import Parser

logger = logging.getLogger(__name__)


class OntologyInitializer():
    def __init__(self, namespace_registry, path=None):
        self.namespace_registry = namespace_registry
        self.path = os.path.join(
            path or os.path.expanduser("~"),
            ".osp_ontologies")
        self.installed_path = os.path.join(self.path, "installed")
        os.makedirs(self.installed_path, exist_ok=True)

    def initialize_installed_ontologies(self, namespace_module):
        """Load the installed ontologies.

        :param use_pickle: Whether to use the provided pickle file,
            defaults to True
        :type use_pickle: bool, optional
        """
        self._create_directories(namespace_module)

        # Load rdf files TODO more efficient loading method
        parser = Parser()
        parser.parse(self.installed_path)
        self.namespace_registry.set_namespaces(
            namespaces=parser.namespaces,
            namespace_module=namespace_module
        )

    def _clean(self, namespace_module):
        if namespace_module._current_path != namespace_module._installed_path:
            logger.info("Removing %s" % namespace_module._current_path)
            shutil.rmtree(namespace_module._current_path)

    def _create_directories(self, namespace_module):
        """Create the necessary directories if they don't exist."""
        for p in [self.path, self.installed_path]:
            if not os.path.exists(p):
                os.mkdir(p)
        namespace_module._main_path = self.path
        namespace_module._installed_path = self.installed_path
        namespace_module._current_path = self.installed_path
