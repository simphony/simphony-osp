from typing import Tuple, Set, Dict, Optional
import io
import logging
import os.path
from rdflib import Graph, URIRef
import rdflib
import requests
import yaml
from osp.core.ontology.parser.parser import OntologyParser
import osp.core.ontology.parser.owl.keywords as keywords

logger = logging.getLogger(__name__)


class OWLParser(OntologyParser):
    # graph: Graph (inherited from OntologyParser)
    _yaml_config: dict

    @property
    def identifier(self) -> str:
        """Get the identifier of the loaded ontology package.

        Returns:
            str: The identifier of the loaded ontology package.
        """
        return self._yaml_config[keywords.IDENTIFIER_KEY].lower()

    @property
    def namespaces(self) -> Dict[str, URIRef]:
        """Get the names of the namespaces of the loaded configuration file.

        Returns:
            Tuple[str]: A tuple containing the defined namespace names.
        """
        return {label.lower(): URIRef(value) for label, value in
                self._yaml_config[keywords.NAMESPACES_KEY].items()}

    @property
    def requirements(self) -> Set[str]:
        requirements = self._yaml_config.get(keywords.REQUIREMENTS_KEY, list())
        if not isinstance(requirements, list):
            raise ValueError(
                f"Object of type {type(requirements)} given as list of "
                f"requirements for the ontology {self.identifier}. You need "
                f"to specify a list."
            )
        return set(requirements)

    @property
    def active_relationships(self) -> Tuple[URIRef]:
        return tuple(rdflib.URIRef(x) for x in
                     self._yaml_config.get(keywords.ACTIVE_REL_KEY, tuple()))

    @property
    def default_relationship(self) -> Optional[URIRef]:
        default_relationship = self._yaml_config.get(keywords.DEFAULT_REL_KEY,
                                                     None)
        return URIRef(default_relationship) if default_relationship else None

    @property
    def reference_style(self) -> bool:
        return self._yaml_config.get(keywords.REFERENCE_STYLE_KEY, False)

    def __init__(self, path: str):
        self._load_yaml_config(path)
        self._load_ontology_graph(self._yaml_config, path)

    def install(self, destination: str):
        """Store the parsed files at the given destination.

        This function is meant to copy the ontology to the OSP-core data
        directory. So usually the destination will be `~/.osp_ontologies`.

        Args:
            destination (str): the OSP-core data directory.
        """
        # TODO: This function is related to exporting ontologies.
        rdf_relative_path = f"{self.identifier}.xml"
        graph_destination = os.path.join(destination, rdf_relative_path)
        config_destination = os.path.join(destination,
                                          f"{self.identifier}.yml")
        saved_graph, saved_config = (False, )*2
        try:
            # Save graph.
            self.graph.serialize(graph_destination,
                                 format='xml')
            saved_graph = True
            # Save YML config.
            yaml_config = self._yaml_config
            yaml_config[keywords.RDF_FILE_KEY] = rdf_relative_path
            yaml_config[keywords.FILE_FORMAT_KEY] = "xml"
            with open(config_destination, 'w') as file:
                yaml.safe_dump(yaml_config, file)
            saved_config = True
        finally:
            if not all((saved_graph, saved_config)):
                if saved_graph:
                    os.remove(graph_destination)
                if saved_config:
                    os.remove(config_destination)

    def _load_yaml_config(self, path: str) -> list:
        """Load the given YAML config file for the OWL ontology.

        Loads the YAML config file into the Parser object. Validates it first.

        Args:
            path (str): path of the YAML config file to load.

        Returns:
            doc (list): YAML doc for the specified config file, validated
                by `_validate_yaml_config`.

        Raises:
            SyntaxError: needed keywords not found in file.
            ValueError: invalid values for some keywords.
        """
        path = self.parse_file_path(path)
        doc = self.load_yaml(path)
        try:
            self._validate_yaml_config(doc)
        except SyntaxError or ValueError as e:
            raise type(e)(f'Invalid configuration file {path}. {e}')
        self._yaml_config = doc
        return doc

    @staticmethod
    def _validate_yaml_config(doc: list):
        """Validate the given YAML config file for the OWL ontology.

        Args:
            doc (list): the path of the YAML config file.

        Raises:
            SyntaxError: needed keywords not found in file.
            ValueError: invalid values for some keywords.
        """
        if not all(KEY in doc for KEY in keywords.MANDATORY_KEYS):
            raise SyntaxError(f"The given file is not a YAML configuration "
                              f"file for an OWL ontology. Make sure that it "
                              f"contains all of the following keys: %s."
                              % ', '.join(KEY
                                          for KEY in keywords.MANDATORY_KEYS))
        other_keys = set(KEY for KEY in doc) - set(keywords.ALL_KEYS)
        if other_keys:
            raise SyntaxError("Specified unknown keys in YAML file: %s"
                              % other_keys)
        if '.' in doc[keywords.IDENTIFIER_KEY]:
            raise ValueError("No dots are allowed in the given package "
                             "identifier: %s." % doc[keywords.IDENTIFIER_KEY])

    def _load_ontology_graph(self,
                             yaml_config_doc: list,
                             yaml_config_path: str) -> Graph:
        """Get the ontology from the file specified in the configuration file.

        Args:
            yaml_config_doc (list): The YAML doc resulting from loading the
                a YAML config file for OWL ontologies. The doc must have been
                validated with `_validate_yaml_config` before being passed to
                this function.
            yaml_config_path (str): the path where the YAML config file was
                read. It is used to resolve the relative path to the ontology
                file.
        Returns:
            Graph: The ontology graph.
        """
        rdf_file_location = yaml_config_doc[keywords.RDF_FILE_KEY]
        if rdf_file_location.startswith(('http://', 'https://')):
            logger.info(f"Downloading {rdf_file_location}.")
            content = requests.get(rdf_file_location).content.decode('utf-8')
            file_like = io.StringIO(content)
        else:
            rdf_file_location = os.path.join(os.path.dirname(yaml_config_path),
                                             rdf_file_location)
            file_like = open(rdf_file_location)
        graph = Graph()
        graph.parse(file_like,
                    format=self._yaml_config.get(keywords.FILE_FORMAT_KEY,
                                                 'xml'))
        file_like.close()
        self.graph = graph
        return graph

