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
        self.current_path = self.installed_path
        os.makedirs(self.installed_path, exist_ok=True)

    def initialize_installed_ontologies(self, ):
        """Load the installed ontologies.

        :param use_pickle: Whether to use the provided pickle file,
            defaults to True
        :type use_pickle: bool, optional
        """

        # Load rdf files TODO more efficient loading method
        self.namespace_registry.load(self.installed_path)
        self.namespace_registry.update_namespaces()

    def _clean(self):
        if self.current_path != self.installed_path:
            logger.info("Removing %s" % self.current_path)
            shutil.rmtree(self.current_path)
