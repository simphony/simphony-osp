from abc import ABC, abstractmethod
from typing import Tuple, Set, Dict, Optional
import logging
import os
from rdflib import Graph, URIRef
import yaml

logging = logging.getLogger(__name__)


class OntologyParser(ABC):
    graph: Graph

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def identifier(self) -> str:
        pass

    @property
    @abstractmethod
    def namespaces(self) -> Dict[str, URIRef]:
        pass

    @property
    @abstractmethod
    def requirements(self) -> Set[str]:
        pass

    @property
    @abstractmethod
    def active_relationships(self) -> Tuple[URIRef]:
        pass

    @property
    @abstractmethod
    def default_relationship(self) -> Optional[URIRef]:
        pass

    @property
    @abstractmethod
    def reference_style(self) -> bool:
        pass

    @abstractmethod
    def install(self, destination: str):
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
            os.path.dirname(__file__), "../docs",
            f"{file_identifier}.ontology.yml"
        )
        b = os.path.join(
            os.path.dirname(__file__), "../docs",
            f"{file_identifier}.yml"
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
        with open(path, 'r') as file:
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
    def is_owl_ontology(doc):
        import osp.core.ontology.parser.owl.keywords as keywords
        return all(x in doc for x in (keywords.RDF_FILE_KEY,
                                      keywords.IDENTIFIER_KEY))

    @classmethod
    def get_parser(cls, path: str) -> 'OntologyParser':
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
    """For backwards compatibility: do not break wrapper's unit tests."""

    def __init__(self, parser_namespace_registry=None):
        from osp.core.ontology.namespace_registry import namespace_registry
        """Initialize the parser.

        Args:
            graph (rdflib.Graph): The graph to add the triples to.
                might already contain some triples.
            parser_namespace_registry (NamespaceRegistry): The namespace
                registry that should be connected to this parser. The parser
                will register the read namespaces in this specific namespace
                registry. If none is provided, then the default
                (namespace_registry from osp.core.ontology.namespace_registry)
                will be used. In fact, you should never create several
                namespace registries, except on unit tests.
        """
        self._namespace_registry = parser_namespace_registry or \
            namespace_registry

    @staticmethod
    def parse(path: str):
        from osp.core.ontology.namespace_registry import namespace_registry
        parser = OntologyParser.get_parser(path)
        namespace_registry.load_parser(parser)
