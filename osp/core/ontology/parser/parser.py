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

        This function is meant to copy the ontology to the OSP-core data
        directory. So usually the destination will be `~/.osp_ontologies`.

        Args:
            destination (str): the OSP-core data directory.
        """
        pass

    @staticmethod
    def parse_file_path(file_identifier: str):
        """Get the correct file path for a given identifier.

        For a given one, i.e. translate non
        paths to osp/core/ontology/docs/*.yml

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
            "../docs",
            f"{file_identifier}.ontology.yml",
        )
        b = os.path.join(
            os.path.dirname(__file__), "../docs", f"{file_identifier}.yml"
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
    def is_yaml_ontology(doc):
        """Check whether the given YAML document is a YAML ontology.

        Args:
            doc (dict): A loaded YAML document.

        Returns:
            bool: Whether the given document is a YAML ontology.
        """
        import osp.core.ontology.parser.yml.keywords as keywords

        return keywords.ONTOLOGY_KEY in doc and keywords.NAMESPACE_KEY in doc

    @staticmethod
    def is_owl_ontology(doc: dict) -> bool:
        """Tells whether a given YAML doc is an OWL ontology config file.

        Args:
            doc (dict): the doc obtained after reading the YAML config file.
        """
        import osp.core.ontology.parser.owl.keywords as keywords

        return all(
            x in doc for x in (keywords.RDF_FILE_KEY, keywords.IDENTIFIER_KEY)
        )

    @classmethod
    def get_parser(cls, path: str) -> "OntologyParser":
        """Parse the given YAML files.

        Args:
            path (str): path to the YAML file
        """
        from osp.core.ontology.parser.owl.parser import OWLParser
        from osp.core.ontology.parser.yml.parser import YMLParser

        file_path = cls.parse_file_path(path)
        yaml_doc = cls.load_yaml(file_path)
        if cls.is_yaml_ontology(yaml_doc):
            parser = YMLParser(file_path)
        elif cls.is_owl_ontology(yaml_doc):
            parser = OWLParser(file_path)
        else:
            raise SyntaxError(f"Invalid format of file {file_path}")
        return parser


class Parser:
    """For backwards compatibility: do not break wrapper's unit tests.

    It is only used on the unit tests, but cannot be moved to the tests'
    folder due to `simdummy_session.py` also using it and being part of the
    osp-core package.

    Do NOT use this class outside the unit tests.
    """

    load_history: Set = set()  # This attribute is mutable on purpose.

    def __init__(self, parser_namespace_registry=None):
        """Initialize the parser.

        Args:
            parser_namespace_registry (NamespaceRegistry): The namespace
                registry that should be connected to this parser. The parser
                will register the read namespaces in this specific namespace
                registry. If none is provided, then the default
                (namespace_registry from osp.core.ontology.namespace_registry)
                will be used. In fact, you should never create several
                namespace registries, except on unit tests.
        """
        from osp.core.ontology.namespace_registry import namespace_registry

        self._namespace_registry = (
            parser_namespace_registry or namespace_registry
        )

    def parse(self, path: str):
        """Directly loads an ontology in the namespace registry.

        The format of the ontology is automatically recognized.

        Args:
            path: The path of the YAML ontology file or OWL ontology YAML
                configuration file to load.
        """
        from osp.core.ontology.namespace_registry import namespace_registry

        parser = OntologyParser.get_parser(path)
        namespace_registry.load_parser(parser)
        if namespace_registry is self._namespace_registry:
            self.load_history.add(path)
