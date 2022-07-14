"""Parses OWL ontologies."""

import io
import logging
import os.path
from typing import Dict, Optional, Set, Union

import requests
import yaml
from rdflib import RDF, RDFS, Graph, URIRef
from rdflib.util import guess_format

import simphony_osp.ontology.parser.owl.keywords as keywords
from simphony_osp.ontology.parser.parser import OntologyParser

logger = logging.getLogger(__name__)


class OWLParser(OntologyParser):
    """Parses OWL ontologies."""

    _file_path: str
    _graph: Optional[Graph] = None  # For lazy evaluation.
    _yaml_config: Union[dict, list]

    def __init__(self, path: str):
        """Initialize the OWL ontology parser."""
        self._yaml_config = self._load_yaml_config(path)
        self._file_path = self.parse_file_path(path)

    @property
    def identifier(self) -> str:
        """Get the identifier of the loaded ontology package.

        Returns:
            The identifier of the loaded ontology package.
        """
        return self._yaml_config[keywords.IDENTIFIER_KEY].lower()

    @property
    def namespaces(self) -> Dict[str, URIRef]:
        """Fetch the namespaces from the ontology files.

        Returns:
            A dictionary containing the defined namespace names and URIs.
        """
        namespaces = {
            label.lower(): URIRef(value)
            for label, value in self._yaml_config[
                keywords.NAMESPACES_KEY
            ].items()
        }
        # TODO: Do not do this, the ontology creator is responsible.
        for name, iri in namespaces.items():
            if not (iri.endswith("#") or iri.endswith("/")):
                namespaces[name] = iri + "#"
        return namespaces

    @property
    def requirements(self) -> Set[str]:
        """Fetch the dependencies from the ontology file."""
        requirements = self._yaml_config.get(keywords.REQUIREMENTS_KEY, list())
        if not isinstance(requirements, list):
            raise ValueError(
                f"Object of type {type(requirements)} given as list of "
                f"requirements for the ontology {self.identifier}. You need "
                f"to specify a list."
            )
        return set(requirements)

    @property
    def graph(self) -> Graph:
        """Fetch the ontology graph from the ontology file."""
        if not self._graph:
            file_format = self._yaml_config.get(keywords.FILE_FORMAT_KEY, None)
            self._graph = self._read_ontology_graph(
                self._yaml_config, self._file_path, file_format
            )
        return self._graph

    def install(self, destination: str):
        """Store the parsed files at the given destination.

        This function is meant to copy the ontology to the SimPhoNy data
        directory. So usually the destination will be `~/.simphony-osp`.

        Args:
            destination: the SimPhoNy data directory.
        """
        # TODO: This function is related to exporting ontologies.
        rdf_relative_path = f"{self.identifier}.xml"
        graph_destination = os.path.join(destination, rdf_relative_path)
        config_destination = os.path.join(
            destination, f"{self.identifier}.yml"
        )
        saved_graph, saved_config = (False,) * 2
        try:
            # Save graph.
            self.graph.serialize(graph_destination, format="xml")
            saved_graph = True
            # Save YML config.
            yaml_config = self._yaml_config
            yaml_config[keywords.RDF_FILE_KEY] = rdf_relative_path
            yaml_config[keywords.FILE_FORMAT_KEY] = "xml"
            with open(config_destination, "w") as file:
                yaml.safe_dump(yaml_config, file)
            saved_config = True
        finally:
            if not all((saved_graph, saved_config)):
                if saved_graph:
                    os.remove(graph_destination)
                if saved_config:
                    os.remove(config_destination)

    @classmethod
    def _load_yaml_config(cls, path: str) -> list:
        """Load the given YAML config file for the OWL ontology.

        Loads the YAML config file into the Parser object. Validates it first.

        Args:
            path: path of the YAML config file to load.

        Returns:
            doc: YAML doc for the specified config file, validated
                by `_validate_yaml_config`.

        Raises:
            SyntaxError: needed keywords not found in file.
            ValueError: invalid values for some keywords.
        """
        path = cls.parse_file_path(path)
        doc = cls.load_yaml(path)
        try:
            cls._validate_yaml_config(doc)
        except SyntaxError or ValueError as e:
            raise type(e)(f"Invalid configuration file {path}. {e}")
        return doc

    @staticmethod
    def _validate_yaml_config(doc: list):
        """Validate the given YAML config file for the OWL ontology.

        Args:
            doc: the path of the YAML config file.

        Raises:
            SyntaxError: needed keywords not found in file.
            ValueError: invalid values for some keywords.
        """
        if not all(KEY in doc for KEY in keywords.MANDATORY_KEYS):
            raise SyntaxError(
                "The given file is not a YAML configuration "
                "file for an OWL ontology. Make sure that it "
                "contains all of the following keys: %s."
                % ", ".join(KEY for KEY in keywords.MANDATORY_KEYS)
            )
        other_keys = {KEY for KEY in doc} - set(keywords.ALL_KEYS)
        if other_keys:
            raise SyntaxError(
                "Specified unknown keys in YAML file: %s" % other_keys
            )
        if "." in doc[keywords.IDENTIFIER_KEY]:
            raise ValueError(
                "No dots are allowed in the given package "
                "identifier: %s." % doc[keywords.IDENTIFIER_KEY]
            )

    @staticmethod
    def _read_ontology_graph(
        yaml_config_doc: dict,
        yaml_config_path: str,
        file_format: Optional[str] = None,
    ) -> Graph:
        """Get the ontology from the file specified in the configuration file.

        Args:
            yaml_config_doc: The YAML doc resulting from loading the YAML
                config file for OWL ontologies. The doc must have been
                validated with `_validate_yaml_config` before being passed to
                this function.
            yaml_config_path: The path where the YAML config file was
                read. It is used to resolve the relative path to the ontology
                file.
            file_format: The format of the file containing the ontology graph.
                When not provided, it will be guessed using `guess_format`
                from `rdflib.util`.

        Returns:
            Graph: The ontology graph.
        """
        rdf_file_location = yaml_config_doc[keywords.RDF_FILE_KEY]
        file_format = file_format or guess_format(rdf_file_location)
        if rdf_file_location.startswith(("http://", "https://")):
            logger.info(f"Downloading {rdf_file_location}.")
            content = requests.get(rdf_file_location).content.decode("utf-8")
            file_like = io.StringIO(content)
        else:
            rdf_file_location = os.path.join(
                os.path.dirname(yaml_config_path), rdf_file_location
            )
            file_like = open(rdf_file_location, "rb")
        graph = Graph()
        graph.parse(file_like, format=file_format)
        file_like.close()

        # Patch DCTERMS, which defines http://purl.org/dc/terms/Agent
        # both as a class and as an instance of
        # http://purl.org/dc/terms/AgentClass
        if (
            URIRef("http://purl.org/dc/terms/"),
            URIRef("http://purl.org/dc/terms/modified"),
            None,
        ) in graph:
            graph.remove(
                (
                    URIRef("http://purl.org/dc/terms/Agent"),
                    RDF.type,
                    URIRef("http://purl.org/dc/terms/AgentClass"),
                )
            )
            graph.add(
                (
                    URIRef("http://purl.org/dc/terms/Agent"),
                    RDFS.subClassOf,
                    URIRef("http://purl.org/dc/terms/AgentClass"),
                )
            )

        return graph
