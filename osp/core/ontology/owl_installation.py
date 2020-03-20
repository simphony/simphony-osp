import os
import re
import rdflib
import subprocess
import logging
import yaml

logger = logging.getLogger(__name__)

OWL_FILES_KEY = "ontology_files"
DOMAIN_MAPPING_KEY = "namespaces"


class OwlInstaller():
    def __init__(self):
        self.graph = rdflib.Graph()
        self.namespaces = dict()
        self.domain_mapping = dict()

    def install(self, file_paths):
        yaml_docs = dict()
        for file_path in list(file_paths):
            with open(file_path, 'r') as stream:
                yaml_doc = yaml.safe_load(stream)
                if OWL_FILES_KEY in yaml_doc:
                    yaml_docs[file_path] = yaml_doc
                    file_paths.remove(file_path)
        self.parse(yaml_docs)

    def parse(self, yaml_docs):
        owl_files = [os.path.join(os.path.dirname(file_path), x)
                     for file_path, yaml_doc in yaml_docs.items()
                     for x in yaml_doc[OWL_FILES_KEY]]
        self.load_owl_files(owl_files)
        self.domain_mapping = {x: y for yaml_doc in yaml_docs.values()
                               for x, y in yaml_doc[DOMAIN_MAPPING_KEY].items()}
        self.build_namespaces()

    def load_owl_files(self, owl_files):
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

    def build_namespaces(self):
        for (s, p, o) in self.graph.triples(
            (None, rdflib.RDF.type, rdflib.OWL.Class)
        ):
            if isinstance(s, rdflib.term.URIRef):
                self.load_entity(s, rdflib.OWL.Class)
        for (s, p, o) in self.graph.triples(
            (None, rdflib.RDF.type, rdflib.OWL.ObjectProperty)
        ):
            if isinstance(s, rdflib.term.URIRef):
                self.load_entity(s, rdflib.OWL.ObjectProperty)
        for (s, p, o) in self.graph.triples(
            (None, rdflib.RDF.type, rdflib.OWL.DataProperty)
        ):
            if isinstance(s, rdflib.term.URIRef):
                self.load_entity(s, rdflib.OWL.DataProperty)

    def load_entity(self, uri, rdf_type):
        for top_namespace, uri_prefix in self.domain_mapping.items():
            if str(uri).startswith(uri_prefix):
                uri_suffix = str(uri)[len(uri_prefix):].strip("/#")
                name = filter(None, re.split("[/#]+", uri_suffix))
                name = map(lambda x: x.split(".")[0], name)
                name = [x.replace("-", "_") for x in name]
                name = [top_namespace] + name
                namespace = ".".join(name[:-1])
                if namespace not in self.namespaces:
                    logger.info("Installed namespace %s" % namespace)
                    self.namespaces[namespace] = dict()
                self.namespaces[namespace][name[-1]] = uri
                logger.debug("Use %s.%s to reference %s"
                             % (namespace, name[-1], uri))
                for (s, p, o) in self.graph.triples((uri, rdflib.RDFS.label, None)):
                    self.namespaces[namespace][str(o)] = uri
                    logger.debug("Use %s.%s to reference %s"
                                 % (namespace, o, uri))
