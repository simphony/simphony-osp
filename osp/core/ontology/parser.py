import os
import rdflib
import logging
import yaml
import requests
import tempfile
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
REFERENCE_STYLE_KEY = "reference_by_label"
ALL_KEYS = set([
    RDF_FILE_KEY, NAMESPACES_KEY, ACTIVE_REL_KEY, DEFAULT_REL_KEY,
    IDENTIFIER_KEY, FILE_FORMAT_KEY, REFERENCE_STYLE_KEY
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
                s = "-" + os.path.basename(file_path)
                with tempfile.NamedTemporaryFile(mode="wt", suffix=s) as f:
                    self._parse_rdf(**self._parse_yml(yaml_doc, file_path, f))
            else:
                raise SyntaxError(f"Invalid format of file {file_path}")
            self._yaml_docs.append(yaml_doc)
        logger.info("Loaded %s ontology triples in total" % len(self.graph))

    def store(self, destination):
        """Store the parsed files at the given destination.

        Args:
            destination (Path): The directory to store the files.
        """
        for yaml_doc in self._yaml_docs:
            identifier = self.get_identifier(yaml_doc)
            # store rdf files
            if not YmlParser.is_yaml_ontology(yaml_doc):
                g = self._graphs[identifier]
                rdf_file = f"{identifier}.xml"
                g.serialize(os.path.join(destination, rdf_file),
                            format="xml")
                yaml_doc[RDF_FILE_KEY] = rdf_file

            # store yaml files
            file_path = os.path.join(destination, f"{identifier}.yml")
            with open(file_path, "w") as f:
                yaml.safe_dump(yaml_doc, f)

    @staticmethod
    def get_identifier(file_path_or_doc):
        """Get the identifier of the given yaml doc or path to such.

        Args:
            file_path_or_doc (Union[Path, dict]): The YAML document or
                a path to it

        Raises:
            SyntaxError: Invalid YAML format

        Returns:
            str: The identifier of the yaml document.
        """
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
        """Get the requirements of a given document or file path to such.

        Args:
            file_path_or_doc (Union[Path, dict]): The YAML document or
                a path to it

        Returns:
            Set[str]: The requirements
        """
        yaml_doc = file_path_or_doc
        if isinstance(file_path_or_doc, str):
            file_path = Parser.get_file_path(file_path_or_doc)
            with open(file_path, "r") as f:
                yaml_doc = yaml.safe_load(f)
        if REQUIREMENTS_KEY in yaml_doc:
            if not isinstance(yaml_doc[REQUIREMENTS_KEY], list):
                identifier = Parser.get_identifier(yaml_doc)
                raise ValueError(
                    f"Object of type {type(yaml_doc[REQUIREMENTS_KEY])} given "
                    f"as list of requirements for ontology {identifier}. "
                    f"You need to specify a list."
                )
            return set(yaml_doc[REQUIREMENTS_KEY])
        else:
            return set()

    @staticmethod
    def get_file_path(file_identifier):
        """Get the correct file path, for a given one, i.e. translate non
        paths to osp/core/ontology/docs/*.yml

        Args:
            file_identifier (str): A filepath or file indentifier

        Returns:
            Path: The translated file path
        """
        if file_identifier.endswith(".yml"):
            return file_identifier
        file_identifier = file_identifier.lower()
        a = os.path.join(
            os.path.dirname(__file__), "docs",
            f"{file_identifier}.ontology.yml"
        )
        b = os.path.join(
            os.path.dirname(__file__), "docs",
            f"{file_identifier}.yml"
        )
        if os.path.exists(a):
            return a
        return b

    def _parse_yml(self, yaml_doc, file_path, f):
        """Parse the owl files specified in the given YAML docs

        Args:
            yaml_doc (dict): Parsed YAML doc that specify
                the ontologies to install
            file_path (str): Location of the corresponding YAML file
            f (str): temporary file to store owl file in case it
                needs to be downloaded
        """
        logger.info("Parsing %s" % file_path)
        if "." in yaml_doc[IDENTIFIER_KEY]:
            raise ValueError("No dot allowed in package identifier. "
                             "Identifier given: %s"
                             % yaml_doc[IDENTIFIER_KEY])

        # download
        if yaml_doc[RDF_FILE_KEY].startswith(("http://", "https://")):
            logger.info(f"Downloading {yaml_doc[RDF_FILE_KEY]}")
            content = requests.get(yaml_doc[RDF_FILE_KEY]) \
                .content.decode("utf-8")
            content = content.replace("xml:lang=\"unibo.it\"",
                                      "xml:lang=\"en\"")
            f.write(content)
            yaml_doc[RDF_FILE_KEY] = f.name
            return yaml_doc

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
            reference_style = kwargs.get(REFERENCE_STYLE_KEY, False)
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
        reference_styles = dict()
        for namespace, iri in namespaces.items():
            if not (
                iri.endswith("#") or iri.endswith("/")
            ):
                iri += "#"
            logger.info(f"You can now use `from osp.core.namespaces import "
                        f"{namespace}`.")
            self.graph.bind(namespace, rdflib.URIRef(iri))
            default_rels[iri] = default_rel
            reference_styles[iri] = reference_style

        self._add_cuba_triples(active_rels)
        self._add_default_rel_triples(default_rels)
        self._add_reference_style_triples(reference_styles)

    def _add_default_rel_triples(self, default_rels):
        """Add the triples to the graph that indicate the default
        relationships per namespace.

        Args:
            default_rels (Dict[str: str]): Mapping from namespace URI to
                default rel URI
        """
        for namespace, default_rel in default_rels.items():
            if default_rel is None:
                continue
            self.graph.add((
                rdflib.URIRef(namespace),
                rdflib_cuba._default_rel,
                rdflib.URIRef(default_rel)
            ))

    def _add_cuba_triples(self, active_rels):
        """Add the triples to connect the owl ontology to CUBA.

        Args:
            active_rels (List[str]): The URIs of the active relationships.
        """
        for rel in active_rels:
            self.graph.add(
                (rdflib.URIRef(rel), rdflib.RDFS.subPropertyOf,
                 rdflib_cuba.activeRelationship)
            )

    def _add_reference_style_triples(self, reference_styles):
        """Add a triple to store how the user should reference the entities
        (by entity or by iri suffix)

        Args:
            reference_styles ([type]): [description]
        """
        for namespace, by_label in reference_styles.items():
            if by_label:
                self.graph.add((
                    rdflib.URIRef(namespace),
                    rdflib_cuba._reference_by_label,
                    rdflib.Literal(True)
                ))
