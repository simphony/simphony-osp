import os
import rdflib
import logging
import yaml
from osp.core.owl_ontology.owl_namespace import OntologyNamespace
from osp.core.owl_ontology.owl_owlapi import OwlApi

logger = logging.getLogger(__name__)

OWL_FILES_KEY = "ontology_files"
NAMESPACES_KEY = "namespaces"


class Parser():
    def __init__(self):
        self.graph = None
        self.iri_namespaces = dict()  # mapping from IRI to namespace name
        self.namespaces = dict()

    def parse(self, *paths):
        """Parse the given YAML files

        Args:
            file_paths (str): path to the YAML files to parse
        """
        print(paths)
        # yaml_docs = dict()
        # for file_path in list(file_paths):
        #     with open(file_path, 'r') as f:
        #         yaml_doc = yaml.safe_load(f)
        #         if OWL_FILES_KEY in yaml_doc:
        #             yaml_docs[file_path] = yaml_doc
        #             file_paths.remove(file_path)
        # owl_files = self._parse_yml(yaml_docs)
        # reasoner = Reasoner()
        # self.graph = reasoner.reason(owl_files)
        # logger.info("Loaded ontology with %s triples" % len(self.graph))
        # self._build_namespaces()
        # return self.namespaces

    def store(self, dir):
        print(dir)

    def parse_reasoned_files(self, yaml_file, rdf_file_paths):
        """Parse the already reasoned RDF files

        Args:
            file_paths (str): path to the RDF files to parse"""
        with open(yaml_file, 'r') as f:
            yaml_doc = yaml.safe_load(f)
            self._parse_yml([yaml_doc])
        self._build_namespaces()
        return self.namespaces

    def _create_settings(self, yaml_docs):
        pass

    def _parse_yml(self, yaml_docs):
        """Parse the owl files specified in the given YAML docs

        Args:
            yaml_docs (dict): Parsed YAML docs that specify
                the ontologies to install
        """
        owl_files = [os.path.join(os.path.dirname(file_path), x)
                     for file_path, yaml_doc in yaml_docs.items()
                     for x in yaml_doc[OWL_FILES_KEY]]
        self.iri_namespaces = {
            (y
             if y.endswith("#") or y.endswith("/")
             else (y + "#")): x
            for yaml_doc in yaml_docs.values()
            for x, y in yaml_doc[NAMESPACES_KEY].items()
        }
        return owl_files

    def _build_namespaces(self):
        """Build the namespace objects"""
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
        iri_namespace, identifier = self._split_iri(iri)
        if str(iri_namespace) in self.iri_namespaces:
            namespace_name = self.iri_namespaces[str(iri_namespace)]
        else:
            logger.warning("The YAML file you provided is incomplete. "
                           "It does not provide a namespace name for %s"
                           % iri_namespace)
            return

        if not identifier.isidentifier():
            logger.warning("The IRI suffix %s of entity %s is not a valid "
                           "python identifier" % (identifier, iri))
        else:
            logger.debug("Use 'from osp.core.namespaces.%s import %s' to "
                         "import entity %s"
                         % (namespace_name, identifier, iri))
        if namespace_name not in self.namespaces:
            self.graph.bind(namespace_name, iri_namespace)
            # graph = rdflib.Graph(self.graph.store, TODO
            #                      rdflib.URIRef(iri_namespace),
            #                      self.graph.namespace_manager)
            self.namespaces[namespace_name] = OntologyNamespace(
                namespace_name, self.graph, iri_namespace)
            logger.info("Created namespace %s" %
                        self.namespaces[namespace_name])

    @staticmethod
    def _split_iri(iri):
        split_char = "#" if "#" in str(iri) else "/"
        split = str(iri).split(split_char)
        namespace = split_char.join(split[:-1]) + split_char
        return rdflib.URIRef(namespace), split[-1]
