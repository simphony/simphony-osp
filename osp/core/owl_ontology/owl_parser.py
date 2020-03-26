import os
import rdflib
import subprocess
import logging
import yaml
from osp.core.owl_ontology.owl_namespace import OntologyNamespace

logger = logging.getLogger(__name__)

OWL_FILES_KEY = "ontology_files"
NAMESPACES_KEY = "namespaces"


class Parser():
    def __init__(self):
        self.graph = rdflib.Graph()
        self.iri_namespaces = dict()  # mapping from IRI to namespace name
        self.namespaces = dict()

    def parse_files(self, file_paths):
        """Parse the given YAML files

        Args:
            file_paths (str): path to the YAML files to parse
        """
        yaml_docs = dict()
        for file_path in list(file_paths):
            with open(file_path, 'r') as stream:
                yaml_doc = yaml.safe_load(stream)
                if OWL_FILES_KEY in yaml_doc:
                    yaml_docs[file_path] = yaml_doc
                    file_paths.remove(file_path)
        return self._parse(yaml_docs)

    def _parse(self, yaml_docs):
        """Parse the owl files specified in the given YAML docs

        Args:
            yaml_docs (dict): Parsed YAML docs that specify
                the ontologies to install
        """
        owl_files = [os.path.join(os.path.dirname(file_path), x)
                     for file_path, yaml_doc in yaml_docs.items()
                     for x in yaml_doc[OWL_FILES_KEY]]
        self._load_owl_files(owl_files)
        self.iri_namespaces = {y: x for yaml_doc in yaml_docs.values()
                                  for x, y in yaml_doc[NAMESPACES_KEY].items()}
        return self._build_namespaces()

    def _load_owl_files(self, owl_files):
        """Load the given owl files

        Args:
            owl_files (str): Path to owl files to load
        """
        java_base = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", "java")
        )
        cmd = [
            "java", "-cp",
            java_base + "/lib/jars/*",
            "-Djava.library.path="
            + java_base + "/lib/so", "org.simphony.OntologyLoader"
        ] + list(owl_files)
        logger.info("Running Reasoner")
        logger.debug(" ".join(cmd))
        subprocess.run(cmd, check=True)

        self.graph.parse("inferred_ontology.owl")
        os.remove("inferred_ontology.owl")
        logger.info("Loaded ontology with %s triples" % len(self.graph))

    def _build_namespaces(self):
        for (s, p, o) in self.graph.triples(
            (None, rdflib.RDF.type, rdflib.OWL.Class)
        ):
            if isinstance(s, rdflib.term.URIRef):
                self._add_entity(s, rdflib.OWL.Class)
        for (s, p, o) in self.graph.triples(
            (None, rdflib.RDF.type, rdflib.OWL.ObjectProperty)
        ):
            if isinstance(s, rdflib.term.URIRef):
                self._add_entity(s, rdflib.OWL.ObjectProperty)
        for (s, p, o) in self.graph.triples(
            (None, rdflib.RDF.type, rdflib.OWL.DataProperty)
        ):
            if isinstance(s, rdflib.term.URIRef):
                self._add_entity(s, rdflib.OWL.DataProperty)

    def _add_entity(self, iri, rdf_type):
        """Create the namespace object of the entity, if it doesn't already exist.

        Args:
            iri (rdflib.URIRef): The IRI if the entity
            rdf_type (Type): The type of the entity
        """
        iri_namespace, identifier = str(iri).split("#")  # TODO also support /
        if iri_namespace not in self.iri_namespaces:
            logger.warning("The YAML file you provided is incomplete. "
                           "It does not provide a namespace name for %s"
                           % iri_namespace)
            return
        namespace_name = self.iri_namespaces[iri_namespace]
        if not identifier.isidentifier():
            logger.warning("The IRI suffix %s of entity %s is not a valid "
                           "python identifier" % identifier, iri)
        else:
            logger.debug("Use 'from osp.core.namespaces.%s import %s' to "
                         "import entity %s"
                         % (namespace_name, identifier, iri))
        if namespace_name not in self.namespaces:
            self.graph.bind(namespace_name, rdflib.URIRef(iri_namespace))
            # graph = rdflib.Graph(self.graph.store, TODO
            #                      rdflib.URIRef(iri_namespace),
            #                      self.graph.namespace_manager)
            self.namespaces[namespace_name] = OntologyNamespace(
                namespace_name, self.graph)
            logger.info("Created namespace %s" %
                        self.namespaces[namespace_name])
        print(self.namespaces[namespace_name].get(identifier))
