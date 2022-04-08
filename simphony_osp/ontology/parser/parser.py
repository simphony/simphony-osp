"""Generic ontology parser abstract class.

Also contains a `Parser` class for backwards compatibility.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Set, Tuple

import yaml
from rdflib import Graph, URIRef

logging = logging.getLogger(__name__)


class OntologyParser(ABC):
    """Generic ontology parser abstract class."""

    graph: Graph

    @abstractmethod
    def __init__(self):
        """Initialize the parser.

        NOTE: It is recommended to do it in such a way that the property
        `graph` is lazily loaded, since its computation can take a significant
        amount of time.
        """
        pass

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Get the identifier of the loaded ontology package.

        Returns:
            str: The identifier of the loaded ontology package.
        """
        pass

    @property
    @abstractmethod
    def namespaces(self) -> Dict[str, URIRef]:
        """Fetch the namespaces from the ontology files.

        Returns:
            Dict[str, URIRef]: A dictionary containing the defined namespace
                names and URIs.
        """
        pass

    @property
    @abstractmethod
    def requirements(self) -> Set[str]:
        """Fetch the requirements from the ontology file."""
        pass

    @property
    @abstractmethod
    def active_relationships(self) -> Tuple[URIRef]:
        """Fetch the active relationships from the ontology file."""
        pass

    @property
    @abstractmethod
    def default_relationship(self) -> Optional[URIRef]:
        """Fetch the default relationship from the ontology file."""
        pass

    @property
    @abstractmethod
    def reference_style(self) -> bool:
        """Whether to reference entities by labels or iri suffix."""
        pass

    @abstractmethod
    def install(self, destination: str):
        """Store the parsed files at the given destination.

        This function is meant to copy the ontology to the SimPhoNy data
        directory. So usually the destination will be `~/.simphony-osp`.

        Args:
            destination (str): the SimPhoNy data directory.
        """
        pass

    @staticmethod
    def parse_file_path(file_identifier: str):
        """Get the correct file path for a given identifier.

        For a given one, i.e. translate non
        paths to osp/core/ontology/files/*.yml

        Args:
            file_identifier (str): A filepath or file identifier

        Returns:
            str: The translated file path
        """
        if file_identifier.endswith(".yml"):
            return file_identifier
        file_identifier = file_identifier.lower()
        a = os.path.join(
            os.path.dirname(__file__),
            "../files",
            f"{file_identifier}.ontology.yml",
        )
        b = os.path.join(
            os.path.dirname(__file__), "../files", f"{file_identifier}.yml"
        )
        if os.path.exists(a):
            return os.path.abspath(a)
        return os.path.abspath(b)

    @staticmethod
    def load_yaml(path: str):
        """Load the given YAML file.

        Args:
            path (str): the path of the YAML file.
        """
        with open(path, "r") as file:
            doc = yaml.safe_load(file)
            if doc is None:
                raise SyntaxError(f"File {path} is empty.")
        return doc

    @staticmethod
    def is_owl_ontology(doc: dict) -> bool:
        """Tells whether a given YAML doc is an OWL ontology config file.

        Args:
            doc (dict): the doc obtained after reading the YAML config file.
        """
        import simphony_osp.ontology.parser.owl.keywords as keywords

        return all(
            x in doc for x in (keywords.RDF_FILE_KEY, keywords.IDENTIFIER_KEY)
        )

    @classmethod
    def get_parser(cls, path: str) -> "OntologyParser":
        """Parse the given YAML files.

        Args:
            path (str): path to the YAML file
        """
        from simphony_osp.ontology.parser.owl.parser import OWLParser

        file_path = cls.parse_file_path(path)
        yaml_doc = cls.load_yaml(file_path)
        if cls.is_owl_ontology(yaml_doc):
            parser = OWLParser(file_path)
        else:
            raise SyntaxError(f"Invalid format of file {file_path}")
        return parser
