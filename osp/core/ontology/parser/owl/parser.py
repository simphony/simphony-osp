"""Parses OWL ontologies."""

import io
import logging
import os.path
from itertools import chain
from typing import Dict, Optional, Set, Tuple

import requests
import yaml
from rdflib import OWL, RDF, RDFS, Graph, URIRef
from rdflib.util import guess_format

import osp.core.ontology.parser.owl.keywords as keywords
import osp.core.warnings as warning_settings
from osp.core.ontology.parser.parser import OntologyParser

logger = logging.getLogger(__name__)


class RDFPropertiesWarning(UserWarning):
    """Shown when an RDF file containing RDF properties is read.

    RDF properties are not supported by OSP-core, and therefore they are
    ignored. This warning should not be shown when RDF properties are also
    doubly defined as OWL object or data properties.
    """


class RDFPropertiesWarningFilter(logging.Filter):
    """Attaches the `RDFPropertiesWarning` class to the records."""

    def filter(self, record):
        """Attaches the `RDFPropertiesWarning` to the records."""
        record.warning_class = RDFPropertiesWarning
        return True


class EmptyOntologyFileError(RuntimeError):
    """Should be raised when reading an ontology file with no entities."""


class OWLParser(OntologyParser):
    """Parses OWL ontologies."""

    _file_path: str
    _graph: Graph = None  # For lazy evaluation.
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
        """Fetch the namespaces from the ontology files.

        Returns:
            Dict[str, URIRef]: A dictionary containing the defined namespace
                names and URIs.
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
        """Fetch the requirements from the ontology file."""
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
        """Fetch the active relationships from the ontology file."""
        return tuple(
            URIRef(x)
            for x in self._yaml_config.get(keywords.ACTIVE_REL_KEY, tuple())
        )

    @property
    def default_relationship(self) -> Optional[URIRef]:
        """Fetch the default relationship from the ontology file."""
        default_relationship = self._yaml_config.get(
            keywords.DEFAULT_REL_KEY, None
        )
        return URIRef(default_relationship) if default_relationship else None

    @property
    def reference_style(self) -> bool:
        """Whether to reference entities by labels or iri suffix."""
        return self._yaml_config.get(keywords.REFERENCE_STYLE_KEY, False)

    @property
    def graph(self) -> Graph:
        """Fetch the ontology graph from the ontology file."""
        if not self._graph:
            file_format = self._yaml_config.get(keywords.FILE_FORMAT_KEY, None)
            self._graph = self._read_ontology_graph(
                self._yaml_config, self._file_path, file_format
            )
            self._validate_graph()
        return self._graph

    def __init__(self, path: str):
        """Initialize the OWL ontology parser."""
        self._yaml_config = self._load_yaml_config(path)
        self._file_path = path

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
            path (str): path of the YAML config file to load.

        Returns:
            doc (list): YAML doc for the specified config file, validated
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
            doc (list): the path of the YAML config file.

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
        other_keys = set(KEY for KEY in doc) - set(keywords.ALL_KEYS)
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
            yaml_config_doc: The YAML doc resulting from loading the
                a YAML config file for OWL ontologies. The doc must have been
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
        return graph

    def _validate_graph(self):
        """Verify that the graph is an OWL ontology or RDFS vocabulary."""
        owl_entities = bool(
            next(
                chain(
                    *(
                        self._graph.subjects(RDF.type, type_)
                        for type_ in {
                            OWL.Class,
                            OWL.DatatypeProperty,
                            OWL.ObjectProperty,
                        }
                    )
                ),
                False,
            )
        )  # True when an OWL entity exists, False otherwise.
        rdfs_classes = bool(
            next(iter(self._graph.subjects(RDF.type, RDFS.Class)), False)
        )  # True when an RDFS class exists, False otherwise.

        rdf_properties = set()
        rdf_properties_count = 0
        max_rdf_properties_in_warning = 5
        for s in self._graph.subjects(RDF.type, RDF.Property):
            has_owl_version = bool(
                next(
                    chain(
                        *(
                            self._graph.subjects(RDF.type, type_)
                            for type_ in {
                                OWL.DatatypeProperty,
                                OWL.ObjectProperty,
                            }
                        )
                    ),
                    False,
                )
            )
            if not has_owl_version:
                if len(rdf_properties) < max_rdf_properties_in_warning:
                    rdf_properties.add(s)
                rdf_properties_count += 1

        if rdf_properties and warning_settings.rdf_properties_warning in (
            True,
            None,
        ):
            warning_text = (
                "The ontology package {package} contains the following RDF "
                "properties: {properties}{more}. \n"
                "As RDF properties are not supported by OSP-core, "
                "the aforementioned properties will be ignored.".format(
                    package=self.identifier,
                    properties=", ".join(
                        (str(identifier) for identifier in rdf_properties)
                    ),
                    more=" and "
                    + str(rdf_properties_count - max_rdf_properties_in_warning)
                    + " more"
                    if rdf_properties_count > max_rdf_properties_in_warning
                    else "",
                )
            )
            if warning_settings.rdf_properties_warning is not None:
                warning_text += (
                    "\n"
                    "You can turn off this warning running "
                    "`import osp.core.warnings as warning_settings; "
                    "warning_settings.rdf_property_warning = False`."
                )
            logger_filter = RDFPropertiesWarningFilter()
            logger.addFilter(logger_filter)
            logger.warning(warning_text)
            logger.removeFilter(logger_filter)
        if not any((owl_entities, rdfs_classes)):
            raise EmptyOntologyFileError(
                f"No ontology entities detected in ontology package "
                f"{self.identifier}. Are you sure it is an OWL ontology or an "
                f"RDFS vocabulary?"
            )
