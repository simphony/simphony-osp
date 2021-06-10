from abc import ABC, abstractmethod
from copy import deepcopy
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
            return a
        return b

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


def load(path: str) -> OntologyParser:
    """Parse the given YAML files.

    Args:
        path (str): path to the YAML file
    """
    from osp.core.ontology.parser.owl.parser import OWLParser
    from osp.core.ontology.parser.yml.parser import YMLParser
    import osp.core.ontology.parser.owl.keywords as owl_keywords
    file_path = OntologyParser.parse_file_path(path)
    yaml_doc = OntologyParser.load_yaml(file_path)
    if YMLParser.is_yaml_ontology(yaml_doc):
        parser = YMLParser(file_path)
    elif all(x in yaml_doc for x in
             (owl_keywords.RDF_FILE_KEY, owl_keywords.IDENTIFIER_KEY)):
        parser = OWLParser(file_path)
    else:
        raise SyntaxError(f"Invalid format of file {file_path}")
    return parser


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
    from osp.core.ontology.parser.yml.parser import YMLParser
    import osp.core.ontology.parser.owl.keywords as owl_keywords
    yaml_doc = file_path_or_doc
    if isinstance(file_path_or_doc, str):
        file_path = OntologyParser.parse_file_path(file_path_or_doc)
        with open(file_path, "r") as f:
            yaml_doc = yaml.safe_load(f)
            if yaml_doc is None:
                raise SyntaxError(
                    f"Empty format of file {file_path_or_doc}"
                )
    if YMLParser.is_yaml_ontology(yaml_doc):
        return YMLParser(file_path).identifier
    elif all(x in yaml_doc for x in
             (owl_keywords.RDF_FILE_KEY, owl_keywords.IDENTIFIER_KEY)):
        return yaml_doc[owl_keywords.IDENTIFIER_KEY].lower()
    else:
        raise SyntaxError(f"Invalid format of file {file_path_or_doc}")


def get_requirements(file_path_or_doc):
    """Get the requirements of a given document or file path to such.

    Args:
        file_path_or_doc (Union[Path, dict]): The YAML document or
            a path to it

    Returns:
        Set[str]: The requirements
    """
    from osp.core.ontology.parser.yml.parser import YMLParser
    import osp.core.ontology.parser.owl.keywords as owl_keywords
    yaml_doc = file_path_or_doc
    if isinstance(file_path_or_doc, str):
        file_path = OntologyParser.parse_file_path(file_path_or_doc)
        with open(file_path, "r") as f:
            yaml_doc = yaml.safe_load(f)
    if owl_keywords.REQUIREMENTS_KEY in yaml_doc:
        if not isinstance(yaml_doc[owl_keywords.REQUIREMENTS_KEY], list):
            identifier = get_identifier(yaml_doc)
            raise ValueError(
                f"Object of type  %s given "
                f"as list of requirements for ontology {identifier}. "
                f"You need to specify a list." %
                type(yaml_doc[owl_keywords.REQUIREMENTS_KEY])
            )
        return set(yaml_doc[owl_keywords.REQUIREMENTS_KEY])
    else:
        return set()
