"""Parses YAML ontologies."""

import logging
import os
from typing import Dict, Optional, Set, Tuple

import yaml
from rdflib import OWL, RDF, RDFS, SKOS, XSD, BNode, Graph, Literal, URIRef
from rdflib.graph import ReadOnlyGraphAggregate

import osp.core.ontology.parser.yml.keywords as keywords
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.datatypes import get_rdflib_datatype
from osp.core.ontology.namespace_registry import namespace_registry
from osp.core.ontology.parser.parser import OntologyParser
from osp.core.ontology.parser.yml.case_insensitivity import (
    get_case_insensitive_alternative as alt,
)
from osp.core.ontology.parser.yml.validator import validate

logger = logging.getLogger(__name__)


class YMLParser(OntologyParser):
    """Parses YAML ontologies."""

    _default_rel: URIRef = None
    _file_path: str
    _graph: Graph  # For lazy evaluation.
    _yaml_doc: dict

    @property
    def identifier(self) -> str:
        """Get the identifier of the loaded ontology package.

        Returns:
            str: The identifier of the loaded ontology package.
        """
        return self._namespace

    @property
    def namespaces(self) -> Dict[str, URIRef]:
        """Fetch the namespaces from the ontology files.

        YAML ontologies can define just one namespace.

        Returns:
            Dict[str, URIRef]: A dictionary containing the defined namespace
                names and URIs. For YAML ontologies this dictionary has just
                one key.
        """
        namespace = self._yaml_doc[keywords.NAMESPACE_KEY].lower()
        return {namespace: URIRef(f"http://www.osp-core.com/{namespace}#")}

    @property
    def requirements(self) -> Set[str]:
        """Fetch the requirements from the ontology file."""
        return set(self._yaml_doc.get(keywords.REQUIREMENTS_KEY, set()))

    @property
    def active_relationships(self) -> Tuple[URIRef]:
        """Fetch the active relationships from the ontology file."""
        return tuple(
            iri
            for iri in self.graph.subjects(
                RDFS.subPropertyOf, rdflib_cuba.activeRelationship
            )
        )

    @property
    def default_relationship(self) -> Optional[URIRef]:
        """Fetch the default relationship from the ontology file."""
        if self.graph:
            pass
        return self._default_rel

    @property
    def reference_style(self) -> bool:
        """Whether to reference entities by labels or iri suffix.

        For YAML ontologies it is only possible to reference them by iri
        suffix.
        """
        return False

    def __init__(self, path: str):
        """Initialize the parser."""
        path = self.parse_file_path(path)
        doc = self.load_yaml(path)
        validate(doc, context="<%s>" % os.path.basename(path))
        self._file_path = path
        self._yaml_doc = doc
        self._graph = Graph()

    @property
    def graph(self):
        """Fetch the ontology graph from the ontology file."""
        if not self._graph:
            self._construct_ontology_graph()
        return self._graph

    def install(self, destination: str):
        """Store the parsed files at the given destination.

        This function is meant to copy the ontology to the OSP-core data
        directory. So usually the destination will be `~/.osp_ontologies`.

        Args:
            destination (str): the OSP-core data directory.
        """
        file_path = os.path.join(destination, f"{self.identifier}.yml")
        with open(file_path, "w") as f:
            yaml.safe_dump(self._yaml_doc, f)

    def _construct_ontology_graph(self):
        logger.debug("Parse the ontology %s" % self._namespace)
        self._ontology_doc = self._yaml_doc[keywords.ONTOLOGY_KEY]
        self._graph = Graph()

        self._graph.bind(self._namespace, self._get_iri())
        types = dict()
        for entity_name, entity_doc in self._ontology_doc.items():
            self._parse_entity(entity_name, entity_doc)
            t = self._validate_entity(entity_name, entity_doc)
            types[entity_name] = t

        self._assert_default_relationship_occurrence()
        self._check_default_rel_definition_on_ontology()
        for entity_name, entity_doc in self._ontology_doc.items():
            # self._load_class_expressions(entity) TODO
            if types[entity_name] == "relationship":
                self._set_inverse(entity_name, entity_doc)
                # TODO
                # self._parse_rel_characteristics(entity_name, entity_doc)
                self._check_default_rel_flag_on_entity(entity_name, entity_doc)
            elif types[entity_name] == "attribute":
                self._set_datatype(entity_name)

        for entity_name, entity_doc in self._ontology_doc.items():
            if types[entity_name] == "class":
                self._add_attributes(entity_name, entity_doc)

    # ⬇ All the functions below just are auxiliary functions for ⬇
    # ⬇ _construct_ontology_graph.                               ⬇

    @property
    def _namespace(self):
        return list(self.namespaces.keys())[0]

    def _parse_entity(self, entity_name: str, entity_doc: dict):
        """Parse an entity into triples.

        Args:
            entity_name(str): The name of the entity to load.
            entity_doc(dict): The part of the YAML document that defines the
                entity.
        """
        logger.debug("Parse entity definition for %s" % entity_name)
        iri = self._get_iri(entity_name)
        if keywords.DESCRIPTION_KEY in entity_doc:
            description = Literal(
                entity_doc[keywords.DESCRIPTION_KEY], lang="en"
            )
            self._graph.add((iri, RDFS.isDefinedBy, description))
        label = Literal(entity_name, lang="en")
        self._graph.add((iri, SKOS.prefLabel, label))
        self._add_type_triple(entity_name, iri)

        # Parse superclasses
        for superclass_doc in entity_doc[keywords.SUPERCLASSES_KEY]:
            self._add_superclass(entity_name, iri, superclass_doc)
        return entity_doc

    def _add_type_triple(self, entity_name, iri):
        """Add a triple describing the type of an entity.

        Args:
            entity_name (str): The name of the entity
            iri (URIRef): The IRI of the entity

        Raises:
            ValueError: Could not determine the type of the given entity.
        """
        queue = [(self._namespace, entity_name)]
        types = set()
        while queue:
            namespace, name = queue.pop()

            # same type as parent
            superclass_iri = self._get_iri(name, namespace, entity_name)
            triple = (superclass_iri, RDF.type, None)
            for _, _, o in ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            ).triples(triple):
                if o in {
                    OWL.Class,
                    RDFS.Class,
                    OWL.ObjectProperty,
                    OWL.DatatypeProperty,
                    OWL.FunctionalProperty,
                }:
                    types.add(o)

            if namespace == self._namespace:
                queue += [
                    self.split_name(x)
                    for x in self._ontology_doc[name][
                        keywords.SUPERCLASSES_KEY
                    ]
                    if isinstance(x, str)
                ]
        if not types:
            raise ValueError(f"Could not determine type of {entity_name}")
        for t in types:
            self._graph.add((iri, RDF.type, t))

    def _add_superclass(self, entity_name, iri, superclass_doc):
        """Add superclass triples to the graph.

        Args:
            entity_name (str): The name of the entity that has superclasses.
            iri (URIRef): The iri of the entity
            superclass_doc (dict): The YAML document describing the
                superclasses.
        """
        if isinstance(superclass_doc, str):
            namespace, superclass_name = self.split_name(superclass_doc)
            superclass_iri = self._get_iri(
                superclass_name, namespace, entity_name
            )
            predicate = RDFS.subPropertyOf
            graph = ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            )
            if (iri, RDF.type, OWL.Class) in graph or (
                iri,
                RDF.type,
                RDFS.Class,
            ) in graph:
                predicate = RDFS.subClassOf

            self._graph.add((iri, predicate, superclass_iri))

    def _get_iri(
        self,
        entity_name=None,
        namespace=None,
        current_entity=None,
        _case_sensitive=False,
        _for_default_rel=False,
    ):
        """Get the iri of the given entity and namespace.

        Args:
            entity_name (str, optional): The entity name. Defaults to None.
            namespace (str, optional): The namespace. Defaults to None.
            current_entity (str, optional): Name of the entity that is
                currently parsed (For printing meaningful warnings).
                Defaults to None.
            _case_sensitive (bool, optional): Whether entities are case
                sensitive. Defaults to False.

        Raises:
            AttributeError: Reference to undefined entity

        Returns:
            URIRef: The iri of the given entity
        """
        namespace = namespace or self._namespace
        namespace = namespace.lower()
        entity_name = entity_name or ""
        try:  # Namespace already in graph?
            ns_iri = next(
                iri
                for name, iri in self._graph.namespaces()
                if name == namespace
            )
        except StopIteration:
            ns_iri = URIRef(f"http://www.osp-core.com/{namespace}#")

        if not entity_name:
            return ns_iri

        iri = ns_iri + entity_name
        # in case of reference by label (EMMO)
        if self.reference_style:
            literal = Literal(entity_name, lang="en")
            try:
                iri = next(
                    s
                    for s, p, o in self._graph.triples(
                        (None, SKOS.prefLabel, literal)
                    )
                    if s.startswith(ns_iri)
                )
            except StopIteration:
                pass

        # check if constructed iri exists
        if (
            namespace == self._namespace
            and entity_name not in self._ontology_doc
        ) or (
            namespace != self._namespace
            and (iri, None, None)
            not in ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            )
        ):
            if _case_sensitive and not _for_default_rel:
                raise AttributeError(
                    f"Reference to undefined entity {namespace}.{entity_name} "
                    f"in definition of {current_entity}"
                )
            else:
                case_sensitive_result = self._get_iri_case_insensitive(
                    entity_name,
                    namespace,
                    current_entity,
                    _for_default_rel=_for_default_rel,
                )
            iri = case_sensitive_result if case_sensitive_result else iri
        return iri

    def _get_iri_case_insensitive(
        self, entity_name, namespace, current_entity, _for_default_rel=False
    ):
        """Try to get iri with alternative naming convention of entity.

        This method is for backwards compatibility only.

        Args:
            entity_name (str): The entity name
            namespace (str): The namespace
            current_entity (str): The current entity, for printing warnings.

        Raises:
            AttributeError: Reference to undefined entity.

        Returns:
            URIRef: The iri of the given entity
        """
        alternative = alt(entity_name, namespace == "cuba")
        if alternative is None and not _for_default_rel:
            raise AttributeError(
                f"Reference to undefined entity {namespace}.{entity_name} "
                f"in definition of {current_entity}"
            )
        try:
            r = self._get_iri(alternative, namespace, current_entity, True)
            logger.warning(
                f"{namespace}.{alternative} is referenced with "
                f"'{namespace}.{entity_name}' in defintion of "
                f"{current_entity}. "
                f"Note that referencing entities will be case sensitive "
                f"in future releases. Additionally, entity names defined "
                f"in YAML ontology are no longer required to be ALL_CAPS. "
                f"You can use the yaml2camelcase "
                f"commandline tool to transform entity names to CamelCase."
            )
            return r
        except AttributeError as e:
            if not _for_default_rel:
                raise AttributeError(
                    f"Referenced undefined entity '{namespace}.{entity_name}' "
                    f"in definition of entity {current_entity}. "
                    f"For backwards compatibility reasons we also  looked for "
                    f"{namespace}.{alternative} and failed."
                ) from e

    @staticmethod
    def split_name(name):
        """Split the name in namespace and entity name.

        Args:
            name (str): namespace.entity_name

        Raises:
            ValueError: Not exactly one '.' in the given name

        Returns:
            Tuple[str, str]: Tuple of namespace and name.
        """
        try:
            a, b = name.split(".")
            return a.lower(), b
        except ValueError as e:
            raise ValueError(
                "Reference to entity '%s' without namespace" % name
            ) from e

    def _add_attributes(self, entity_name, entity_doc):
        """Add a attribute to an ontology class.

        Args:
            entity_name (str): The name of the entity to add attributes to.
            entity_doc (dict): The YAML document describing the entity.

        Raises:
            ValueError: Invalid attribute specified.
        """
        iri = self._get_iri(entity_name)
        attributes_def = None
        if keywords.ATTRIBUTES_KEY in entity_doc:
            attributes_def = entity_doc[keywords.ATTRIBUTES_KEY]

        if attributes_def is None:
            return

        # Add the attributes one by one
        for attribute_name, default in attributes_def.items():
            attribute_namespace, attribute_name = self.split_name(
                attribute_name
            )

            attribute_iri = self._get_iri(
                attribute_name, attribute_namespace, entity_name
            )
            x = (attribute_iri, RDF.type, OWL.DatatypeProperty)
            if x not in ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            ):
                raise ValueError(
                    f"Invalid attribute {attribute_namespace}."
                    f"{attribute_name} of entity {entity_name}"
                )
            self._add_attribute(iri, attribute_iri, default)

    def _add_attribute(self, class_iri, attribute_iri, default):
        """Add triples to add a single attribute to a class.

        Args:
            class_iri (URIRef): The URI of the class to add attributes to.
            attribute_iri (URIRef): The IRI of the attribute to add
            default (Any): The default value.
        """
        bnode = BNode()
        self._graph.add((class_iri, RDFS.subClassOf, bnode))
        self._graph.add((bnode, RDF.type, OWL.Restriction))
        self._graph.add(
            (bnode, OWL.cardinality, Literal(1, datatype=XSD.integer))
        )
        self._graph.add((bnode, OWL.onProperty, attribute_iri))

        if default is not None:
            bnode = BNode()
            self._graph.add((class_iri, rdflib_cuba._default, bnode))
            self._graph.add(
                (bnode, rdflib_cuba._default_attribute, attribute_iri)
            )
            self._graph.add(
                (bnode, rdflib_cuba._default_value, Literal(default))
            )

    def _set_inverse(self, entity_name, entity_doc):
        """Set a triple describing the inverse of relationship entity.

        Args:
            entity_name (str): The name of the relationship entity.
            entity_doc (dict): The YAML doc describing the entity.

        Raises:
            RuntimeError: [description]
        """
        if keywords.INVERSE_KEY not in entity_doc:
            return
        inverse_def = entity_doc[keywords.INVERSE_KEY]

        # inverse is defined
        inverse_namespace, inverse_name = self.split_name(inverse_def)
        # if inverse.inverse and inverse.inverse != entity:  TODO
        #     raise RuntimeError(
        #         "Conflicting inverses for %s, %s, %s"
        #         % (entity, inverse, inverse.inverse)
        #     )
        inverse_iri = self._get_iri(
            inverse_name, inverse_namespace, entity_name
        )
        iri = self._get_iri(entity_name)
        self._graph.add((iri, OWL.inverseOf, inverse_iri))

    def _assert_default_relationship_occurrence(self):
        """Assures that only one default relationship is defined in the yaml.

        :raises ValueError: If more than one definition is found.
        """
        occurrences = 0
        if keywords.DEFAULT_REL_KEY in self._yaml_doc:
            occurrences += 1
        for entity_name, entity_doc in self._ontology_doc.items():
            if entity_doc.get(keywords.DEFAULT_REL_KEY) is True:
                occurrences += 1
        if occurrences > 1:
            raise ValueError(
                f"You have defined {occurrences} default relationships for "
                f"namespace {self._namespace} although <= 1 are allowed."
            )

    def _check_default_rel_definition_on_ontology(self):
        """Check if the given yaml defines a default relationship.

        If yes, save that accordingly.
        """
        if keywords.DEFAULT_REL_KEY in self._yaml_doc:
            namespace, entity_name = self._yaml_doc[
                keywords.DEFAULT_REL_KEY
            ].split(".")

            self._default_rel = self._get_iri(
                namespace=namespace,
                entity_name=entity_name,
                _for_default_rel=True,
            )

    def _check_default_rel_flag_on_entity(self, entity_name, entity_doc):
        """Check if the given relationship is the default.

        When it is a default, save that accordingly.

        Args:
            entity_name (str): The name of the relationship entity.
            entity_doc (dict): The YAML doc describing the entity.
        """
        if (
            keywords.DEFAULT_REL_KEY in entity_doc
            and entity_doc[keywords.DEFAULT_REL_KEY]
        ):
            self._default_rel = self._get_iri(entity_name)

    def _set_datatype(self, entity_name):
        """Add triples that specify the datatype of an attribute entity.

        Args:
            entity_name (str): The name of the datatype entity.
        """
        ontology_doc = self._ontology_doc
        entity_doc = ontology_doc[entity_name]

        datatype_def = None
        if keywords.DATATYPE_KEY in entity_doc:
            datatype_def = entity_doc[keywords.DATATYPE_KEY]

        if datatype_def is not None:
            self._graph.add(
                (
                    self._get_iri(entity_name),
                    RDFS.range,
                    get_rdflib_datatype(datatype_def, self._graph),
                )
            )

    def _validate_entity(self, entity_name, entity_doc):
        """Validate the yaml definition of an entity.

        Will check for the special keywords of the different entity types.

        Args:
            entity_name (str): The name of the entity
            entity_doc (dict): The YAML doc describing the entity.

        Raises:
            RuntimeError: Could not deterimine type of entity.

        Returns:
            str: Type of entity
        """
        iri = self._get_iri(entity_name)
        class_triple = (iri, RDF.type, OWL.Class)
        rel_triple = (iri, RDF.type, OWL.ObjectProperty)
        attr_triple = (iri, RDF.type, OWL.DatatypeProperty)
        status = (
            class_triple
            in ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            ),
            rel_triple
            in ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            ),
            attr_triple
            in ReadOnlyGraphAggregate(
                [self._graph, namespace_registry._graph]
            ),
        )
        if sum(status) != 1:
            raise RuntimeError(f"Couldn't determine type of {entity_name}")
        if status[0]:
            t = "class"
        elif status[1]:
            t = "relationship"
        else:
            t = "attribute"

        validate(
            entity_doc,
            t + "_def",
            context="<%s>/ONTOLOGY/%s"
            % (os.path.basename(self._file_path), entity_name),
        )
        return t
