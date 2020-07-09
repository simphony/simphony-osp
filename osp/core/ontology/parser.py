import os
import rdflib
import logging
import yaml
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.yml.yml_parser import YmlParser

logger = logging.getLogger(__name__)

IDENTIFIER_KEY = "identifier"
RDF_FILE_KEY = "ontology_file"
NAMESPACES_KEY = "namespaces"
ACTIVE_REL_KEY = "active_relationships"
DEFAULT_REL_KEY = "default_relationship"
FILE_FORMAT_KEY = "format"
REQUIREMENTS_KEY = "requirements"
ALL_KEYS = set([
    RDF_FILE_KEY, NAMESPACES_KEY, ACTIVE_REL_KEY, DEFAULT_REL_KEY,
    IDENTIFIER_KEY, FILE_FORMAT_KEY
])


class Parser():
    def __init__(self, graph):
        self.graph = graph
        self._yaml_docs = list()
        self._graphs = dict()

    def parse(self, file_path):
        """Parse the given YAML files

        Args:
            file_path (str): path to the YAML file
        """
        file_path = self.get_file_path(file_path)
        with open(file_path, 'r') as f:
            yaml_doc = yaml.safe_load(f)
            if YmlParser.is_yaml_ontology(yaml_doc):
                YmlParser(self.graph).parse(file_path, yaml_doc)
            elif RDF_FILE_KEY in yaml_doc and IDENTIFIER_KEY in yaml_doc:
                self._parse_rdf(**self._parse_yml(yaml_doc, file_path))
            else:
                raise SyntaxError(f"Invalid format of file {file_path}")
            self._yaml_docs.append(yaml_doc)
        logger.info("Loaded %s ontology triples in total" % len(self.graph))

    def store(self, destination):
        for yaml_doc in self._yaml_docs:
            identifier = self.get_identifier(yaml_doc)
            # store rdf files
            if not YmlParser.is_yaml_ontology(yaml_doc):
                g = self._graphs[identifier]
                rdf_file = f"{identifier}.ttl"
                g.serialize(os.path.join(destination, rdf_file),
                            format="ttl")
                yaml_doc[RDF_FILE_KEY] = rdf_file

            # store yaml files
            file_path = os.path.join(destination, f"{identifier}.yml")
            with open(file_path, "w") as f:
                yaml.safe_dump(yaml_doc, f)

    @staticmethod
    def get_identifier(file_path_or_doc):
        yaml_doc = file_path_or_doc
        if isinstance(file_path_or_doc, str):
            file_path = Parser.get_file_path(file_path_or_doc)
            with open(file_path, "r") as f:
                yaml_doc = yaml.safe_load(f)
        if YmlParser.is_yaml_ontology(yaml_doc):
            return YmlParser.get_namespace_name(yaml_doc)
        elif RDF_FILE_KEY in yaml_doc and IDENTIFIER_KEY in yaml_doc:
            return yaml_doc[IDENTIFIER_KEY].lower()
        else:
            raise SyntaxError(f"Invalid format of file {file_path_or_doc}")

    @staticmethod
    def get_requirements(file_path_or_doc):
        yaml_doc = file_path_or_doc
        if isinstance(file_path_or_doc, str):
            file_path = Parser.get_file_path(file_path_or_doc)
            with open(file_path, "r") as f:
                yaml_doc = yaml.safe_load(f)
        if REQUIREMENTS_KEY in yaml_doc:
            return set(yaml_doc[REQUIREMENTS_KEY])
        else:
            return set()

    @staticmethod
    def get_file_path(file_path):
        if file_path.endswith(".yml"):
            return file_path
        file_path = file_path.lower()
        return os.path.join(
            os.path.dirname(__file__), "docs", f"{file_path}.ontology.yml"
        )

    def _parse_yml(self, yaml_doc, file_path):
        """Parse the owl files specified in the given YAML docs

        Args:
            yaml_doc (dict): Parsed YAML doc that specify
                the ontologies to install
            file_path (str): Location of the corresponding YAML file
        """
        logger.info("Parsing %s" % file_path)
        if "." in yaml_doc[IDENTIFIER_KEY]:
            raise ValueError("No dot allowed in package identifier. "
                             "Identifier given: %s"
                             % yaml_doc[IDENTIFIER_KEY])
        yaml_doc[RDF_FILE_KEY] = os.path.join(os.path.dirname(file_path),
                                              yaml_doc[RDF_FILE_KEY])
        return yaml_doc

    def _parse_rdf(self, **kwargs):
        """Parse the RDF files specified in the kwargs.

        Args:
            kwargs (dict[str, Any]): The keyword arguments usually specified
                in a yaml file.
        """
        # parse input kwargs
        try:
            rdf_file = kwargs[RDF_FILE_KEY]
            namespaces = kwargs[NAMESPACES_KEY]
            identifier = kwargs[IDENTIFIER_KEY]
            active_rels = kwargs.get(ACTIVE_REL_KEY, [])
            default_rel = kwargs.get(DEFAULT_REL_KEY, None)
            file_format = kwargs.get(FILE_FORMAT_KEY, "xml")
        except KeyError as e:
            raise TypeError(
                f"Didn't specify necessary parameter {e}. "
                f"Check your YAML file.") from e
        other_keys = set(kwargs.keys()) - ALL_KEYS
        if other_keys:
            raise TypeError("Specified unknown keys in YAML file: %s"
                            % other_keys)

        # parse the files
        logger.info("Parsing %s" % rdf_file)
        self._graphs[identifier] = rdflib.Graph()
        self._graphs[identifier].parse(rdf_file, format=file_format)
        self.graph.parse(rdf_file, format=file_format)
        default_rels = dict()
        for namespace, iri in namespaces.items():
            if not (
                iri.endswith("#") or iri.endswith("/")
            ):
                iri += "#"
            logger.debug("Create namespace %s" % namespace)
            self.graph.bind(namespace, rdflib.URIRef(iri))
            default_rels[iri] = default_rel

        self._add_cuba_triples(active_rels)
        self._add_default_rel_triples(default_rels)

    def _add_default_rel_triples(self, default_rels):
        for namespace, default_rel in default_rels.items():
            if default_rel is None:
                continue
            self.graph.add((
                rdflib.URIRef(namespace),
                rdflib_cuba._default_rel,
                rdflib.URIRef(default_rel)
            ))

    def _add_cuba_triples(self, active_rels):
        for rel in active_rels:
            self.graph.add(
                (rdflib.URIRef(rel), rdflib.RDFS.subPropertyOf,
                 rdflib_cuba.activeRelationship)
            )
