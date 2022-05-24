"""Generic ontology parser abstract class.

Also contains a `Parser` class for backwards compatibility.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Set, Union

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

    @abstractmethod
    def install(self, destination: Union[str, Path]) -> None:
        """Store the parsed files at the given destination.

        This function is meant to copy the ontology to the SimPhoNy data
        directory. So usually the destination will be `~/.simphony-osp`.

        Args:
            destination: the SimPhoNy data directory.
        """
        pass

    @staticmethod
    def parse_file_path(file_identifier: Union[str, Path]) -> str:
        """Get the correct file path for a given identifier.

        For a given one, i.e. translate non
        paths to osp/core/ontology/files/*.yml

        Args:
            file_identifier: A filepath or file identifier.

        Returns:
            The translated file path.
        """
        file_identifier = Path(file_identifier)
        if str(file_identifier).endswith(".yml"):
            return str(file_identifier)
        file_identifier = str(file_identifier).lower()
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
    def load_yaml(path: Union[str, Path]):
        """Load the given YAML file.

        Args:
            path: the path of the YAML file.
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
            doc: the doc obtained after reading the YAML config file.
        """
        import simphony_osp.ontology.parser.owl.keywords as keywords

        return all(
            x in doc for x in (keywords.RDF_FILE_KEY, keywords.IDENTIFIER_KEY)
        )

    @classmethod
    def get_parser(cls, path: Union[str, Path]) -> OntologyParser:
        """Parse the given YAML files.

        Args:
            path: path to the YAML file
        """
        from simphony_osp.ontology.parser.owl.parser import OWLParser

        file_path = cls.parse_file_path(path)
        yaml_doc = cls.load_yaml(file_path)
        if cls.is_owl_ontology(yaml_doc):
            parser = OWLParser(file_path)
        else:
            raise SyntaxError(f"Invalid format of file {file_path}")
        return parser
