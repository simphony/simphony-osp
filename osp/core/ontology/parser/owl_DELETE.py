"""The parser used to parse OWL ontologies in RDF format."""

import os
import rdflib
import logging
import yaml
import requests
import tempfile
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.parser.yml.parser_YML_DELETE import YmlParser
from osp.core.ontology.namespace_registry import namespace_registry

logger = logging.getLogger(__name__)

class Parser():
    """The parser used to parse OWL ontologies in RDF format."""

    def parse(self, file_path):
        # TODO: GOES TO A GENERALIZED PARSER?
        """Parse the given YAML files.

        Args:
            file_path (str): path to the YAML file
        """
        file_path = self.get_file_path(file_path)
        with open(file_path, 'r') as f:
            yaml_doc = yaml.safe_load(f)
            if yaml_doc is None:
                raise SyntaxError(
                    f"Empty format of file {file_path}"
                )
            if YmlParser.is_yaml_ontology(yaml_doc):
                YmlParser(parser_namespace_registry=self._namespace_registry)\
                    .parse(file_path, yaml_doc)
            elif RDF_FILE_KEY in yaml_doc and IDENTIFIER_KEY in yaml_doc:
                s = "-" + os.path.basename(file_path).split(".")[0]
                with tempfile.NamedTemporaryFile(mode="wb+", suffix=s) as f:
                    self._parse_rdf(**self._parse_yml(yaml_doc, file_path, f),
                                    file=f)
            else:
                raise SyntaxError(f"Invalid format of file {file_path}")
            self._yaml_docs.append(yaml_doc)
        logger.info("Loaded %s ontology triples in total" % len(self.graph))

    def _parse_rdf(self, **kwargs):
        # TODO: Task of the general parser.
        """Parse the RDF files specified in the kwargs.

        Args:
            kwargs (dict[str, Any]): The keyword arguments usually specified
                in a yaml file.
        """
        # parse input kwargs
        try:
            rdf_file = kwargs[RDF_FILE_KEY]
            f = kwargs[FILE_HANDLER_KEY]
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

        # parse the files
        logger.info("Parsing %s" % rdf_file)
        self._graphs[identifier] = rdflib.Graph()
        f.seek(0)
        if os.stat(f.name).st_size > 0:
            self._graphs[identifier].parse(f, format=file_format)
        else:
            self._graphs[identifier].parse(rdf_file, format=file_format)
        if reference_style:
            for namespace, iri in namespaces.items():
                self._check_duplicate_labels(iri, identifier)
        for triple in self._graphs[identifier]:
            self.graph.add(triple)
        default_rels = dict()
        reference_styles = dict()
        namespace_iris = set()
        for namespace, iri in namespaces.items():
            if not (
                iri.endswith("#") or iri.endswith("/")
            ):
                iri += "#"
            namespace_iris.add(iri)
            logger.info(f"You can now use `from osp.core.namespaces import "
                        f"{namespace}`.")
            self._namespace_registry.bind(namespace, rdflib.URIRef(iri))
            default_rels[iri] = default_rel
            reference_styles[iri] = reference_style

        self._check_namespaces(namespace_iris)
        self._add_cuba_triples(active_rels)
        self._add_default_rel_triples(default_rels)
        self._add_reference_style_triples(reference_styles)
