import os
import logging
import yaml
import rdflib
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.datatypes import get_rdflib_datatype
from osp.core.ontology.yml.yml_keywords import (
    ONTOLOGY_KEY, NAMESPACE_KEY,
    ROOT_RELATIONSHIP, ROOT_ATTRIBUTE, DESCRIPTION_KEY, SUPERCLASSES_KEY,
    INVERSE_KEY, DEFAULT_REL_KEY, DATATYPE_KEY, ATTRIBUTES_KEY, DISJOINTS_KEY,
    EQUIVALENT_TO_KEY, DOMAIN_KEY, RANGE_KEY, CHARACTERISTICS_KEY,
    MAIN_NAMESPACE, CARDINALITY_KEY, TARGET_KEY, EXCLUSIVE_KEY, AUTHOR_KEY,
    VERSION_KEY, ROOT_CLASS
)
from osp.core.ontology.yml.yml_validator import validate

logger = logging.getLogger(__name__)


class YmlParser:
    """
    Class that parses a YAML file and finds information about the entities
    contained.
    """

    def __init__(self, graph):
        self._doc = None
        self._ontology_doc = None
        self._namespace = None
        self._file_path = None
        self.graph = graph

    @staticmethod
    def is_yaml_ontology(doc):
        return ONTOLOGY_KEY in doc and NAMESPACE_KEY in doc

    @staticmethod
    def get_namespace_name(doc):
        return doc[NAMESPACE_KEY]

    def parse(self, file_path, doc=None):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        logger.info("Parsing YAML ontology file %s" % file_path)
        self._doc = doc or self.get_doc(file_path)
        validate(self._doc,
                 context="<%s>" % os.path.basename(file_path))

        # TODO version and author
        self._file_path = file_path
        self._namespace = self._doc[NAMESPACE_KEY]
        self._ontology_doc = self._doc[ONTOLOGY_KEY]
        self._parse_ontology()

    @staticmethod
    def get_doc(file_path):
        """Parse the file path to yaml

        :param file_path: The path to the file to parse.
        :type file_path: str
        """
        with open(file_path, 'r') as stream:
            yaml_doc = yaml.safe_load(stream)
        return yaml_doc

    def _parse_ontology(self):
        """Parse the entity descriptions."""
        logger.debug("Parse the ontology %s" % self._namespace)

        self.graph.bind(self._namespace, self._get_iri())
        types = dict()
        for entity_name, entity_doc in self._ontology_doc.items():
            self._load_entity(entity_name, entity_doc)
            t = self._validate_entity(entity_name, entity_doc)
            types[entity_name] = t

        for entity_name, entity_doc in self._ontology_doc.items():
            # self._load_class_expressions(entity) TODO
            if types[entity_name] == "class":
                self._add_attributes(entity_name, entity_doc)
            elif types[entity_name] == "relationship":
                self._set_inverse(entity_name, entity_doc)
            #     self._parse_rel_characteristics(entity_name, entity_doc) TODO
                self._check_default_rel(entity_name, entity_doc)
            else:
                self._set_datatype(entity_name, entity_doc)
        # for entity in missing_inverse:  TODO
        #     self._create_missing_inverse(entity)
        # self._validate_parsed_datastructure(self._ontology_namespace)

    @staticmethod
    def split_name(name):
        try:
            a, b = name.split(".")
            return a, b
        except ValueError as e:
            raise ValueError("Reference to entity '%s' without namespace"
                             % name) from e

    def _load_entity(self, entity_name, entity_doc):
        """Load an entity into the registry

        :param entity_name: The name of the entity to load.
        :type entity_name: str
        """
        logger.debug("Parse entity definition for %s" % entity_name)
        iri = self._get_iri(entity_name)
        if DESCRIPTION_KEY in entity_doc:
            description = rdflib.Literal(entity_doc[DESCRIPTION_KEY])
            self.graph.add((iri, rdflib.RDFS.isDefinedBy, description))
        self._add_type_triple(entity_name, iri)

        # Parse superclasses
        for superclass_doc in entity_doc[SUPERCLASSES_KEY]:
            self._add_superclass(entity_name, iri, superclass_doc)
        return entity_doc

    def _get_iri(self, entity_name=None, namespace=None):
        namespace = namespace or self._namespace
        entity_name = entity_name or ""
        return rdflib.URIRef(
            f"http://www.osp-core.com/{namespace}#{entity_name}"
        )

    def _add_superclass(self, entity_name, iri, superclass_doc):
        if isinstance(superclass_doc, str):
            namespace, superclass_name = self.split_name(superclass_doc)
            if (
                namespace == self._namespace
                and superclass_name not in self._ontology_doc
            ):
                raise KeyError(
                    "Reference to undefined entity %s in definition of %s"
                    % (superclass_name, entity_name)
                )
            predicate = rdflib.RDFS.subPropertyOf
            if (iri, rdflib.RDF.type, rdflib.OWL.Class) in self.graph:
                predicate = rdflib.RDFS.subClassOf

            self.graph.add((iri, predicate,
                            self._get_iri(superclass_name, namespace)))

    def _add_type_triple(self, entity_name, iri):
        queue = [(self._namespace, entity_name)]
        types = set()
        while queue:
            namespace, name = queue.pop()

            # same type as parent
            superclass_iri = self._get_iri(name, namespace)
            triple = (superclass_iri, rdflib.RDF.type, None)
            for _, _, o in self.graph.triples(triple):
                types.add(o)

            if namespace == self._namespace:
                queue += [self.split_name(x)
                          for x in self._ontology_doc[name][SUPERCLASSES_KEY]
                          if isinstance(x, str)]
        if not types:
            raise ValueError(f"Could not determine type of {entity_name}")
        for t in types:
            self.graph.add((iri, rdflib.RDF.type, t))

    # def _load_class_expressions(self, entity):
    #     """Load class expressions.

    #     :param entity_name: The name of the entity to load.
    #     :type entity_name: str
    #     """
    #     logger.debug("Parse class expressions for %s" % entity)
    #     ontology_doc = self._ontology_doc
    #     entity_doc = ontology_doc[entity.name]

    #     # The keywords containing the class expressions
    #     if isinstance(entity, OntologyClass):
    #         keywords = [SUPERCLASSES_KEY, EQUIVALENT_TO_KEY, DISJOINTS_KEY]
    #     elif isinstance(entity, OntologyRelationship):
    #         keywords = [DOMAIN_KEY, RANGE_KEY]
    #     else:
    #         return

    #     # Parse the class expression for each keyword
    #     for keyword in keywords:
    #         if keyword not in entity_doc:
    #             continue
    #         ce_yaml = entity_doc[keyword]
    #         if not isinstance(ce_yaml, list):
    #             ce_yaml = [ce_yaml]

    #         for ce in ce_yaml:
    #             entity._add_class_expression(
    #                 keyword, self._parse_class_expression(ce)
    #             )

    def _add_attributes(self, entity_name, entity_doc):
        """Add a attribute to an ontology class

        :param entity: The ontology to add the attributes to
        :type entity: OntologyClass
        """
        iri = self._get_iri(entity_name)
        attributes_def = None
        if ATTRIBUTES_KEY in entity_doc:
            attributes_def = entity_doc[ATTRIBUTES_KEY]

        if attributes_def is None:
            return

        # Add the attributes one by one
        for attribute_name, default in attributes_def.items():
            attribute_namespace, attribute_name = \
                self.split_name(attribute_name)

            attribute_iri = self._get_iri(attribute_name, attribute_namespace)
            x = (attribute_iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
            if x not in self.graph:
                raise ValueError(f"Invalid attribute {attribute_namespace}."
                                 f"{attribute_name} of entity {entity_name}")
            self._add_attribute(iri, attribute_iri, default)

    def _add_attribute(self, class_iri, attribute_iri, default):
        self.graph.add(  # TODO CRITICAL wrong if multiple have same attribute
            (attribute_iri, rdflib.RDFS.domain, class_iri)
        )
        if default is not None:
            bnode = rdflib.BNode()
            self.graph.add((class_iri, rdflib_cuba._default, bnode))
            self.graph.add(
                (bnode, rdflib_cuba._default_attribute, attribute_iri))
            self.graph.add(
                (bnode, rdflib_cuba._default_value, rdflib.Literal(default)))

    def _set_inverse(self, entity_name, entity_doc):
        if INVERSE_KEY not in entity_doc:
            return
        inverse_def = entity_doc[INVERSE_KEY]

        # inverse is defined
        inverse_namespace, inverse_name = self.split_name(inverse_def)
        # if inverse.inverse and inverse.inverse != entity:  TODO
        #     raise RuntimeError(
        #         "Conflicting inverses for %s, %s, %s"
        #         % (entity, inverse, inverse.inverse)
        #     )
        inverse_iri = self._get_iri(inverse_name, inverse_namespace)
        iri = self._get_iri(entity_name)
        self.graph.add(
            (iri, rdflib.OWL.inverseOf, inverse_iri)
        )

    def _check_default_rel(self, entity_name, entity_doc):
        """Check of the given relationship the default
        When it is a default, save that accordingly.

        :param entity: The relationship to check
        :type entity: OntologyRelationship
        """
        if DEFAULT_REL_KEY in entity_doc \
                and entity_doc[DEFAULT_REL_KEY]:
            self.graph.add(
                (self._get_iri(), rdflib_cuba._default_rel,
                 self._get_iri(entity_name))
            )

    def _set_datatype(self, entity_name, entity_doc):
        """Set the datatype of a attribute TODO docstring
        """
        ontology_doc = self._ontology_doc
        entity_doc = ontology_doc[entity_name]

        datatype_def = None
        if DATATYPE_KEY in entity_doc:
            datatype_def = entity_doc[DATATYPE_KEY]

        if datatype_def is not None:
            self.graph.add(
                (self._get_iri(entity_name), rdflib.RDFS.range, 
                 get_rdflib_datatype(self.graph, datatype_def))
            )

    def _validate_entity(self, entity_name, entity_doc):
        """Validate the yaml definition of an entity.
        Will check for the special keywords of the different entity types.
        TODO docstring
        """
        iri = self._get_iri(entity_name)
        class_triple = (iri, rdflib.RDF.type, rdflib.OWL.Class)
        rel_triple = (iri, rdflib.RDF.type, rdflib.OWL.ObjectProperty)
        attr_triple = (iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
        status = (
            class_triple in self.graph,
            rel_triple in self.graph,
            attr_triple in self.graph
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
            entity_doc, t + "_def",
            context="<%s>/ONTOLOGY/%s" % (os.path.basename(self._file_path),
                                          entity_name)
        )
        return t

    # def _parse_rel_characteristics(self, entity):
    #     """Parse the characteristics of a relationship

    #     :param entity: The relationship to parse the characteristics for.
    #     :type entity: OntologyRelationship
    #     """
    #     ontology_doc = self._ontology_doc
    #     entity_doc = ontology_doc[entity.name]
    #     if CHARACTERISTICS_KEY not in entity_doc:
    #         return
    #     characteristics = entity_doc[CHARACTERISTICS_KEY]
    #     for c in characteristics:
    #         entity._add_characteristic(c)

    # def _parse_class_expression(self, yaml_ce):
    #     """Recursively parse a class expression in yaml format.

    #     :param yaml_ce: The yaml expression to parse
    #     :type yaml_ce: Union[str, Dict, List]
    #     :raises ValueError: Invalid expression
    #     :return: The parsed class expression.
    #     :rtype: ClassExpression
    #     """
    #     logger.debug("Parse class expression %s" % yaml_ce)
    #     if isinstance(yaml_ce, str):
    #         return self._parse_oclass_ce(yaml_ce)

    #     if isinstance(yaml_ce, dict) and len(yaml_ce) != 1:
    #         raise ValueError(
    #             "Invalid dictionary call expression: %s. "
    #             "A class expression that is a dictionary is only allowed to "
    #             "have at most one key. You should probably transform it to a "
    #             "list of dictionaries." % yaml_ce
    #         )
    #     key = next(iter(yaml_ce.keys()))
    #     if key.lower() in OPERATORS:
    #         return self._parse_operator_ce(yaml_ce, key)
    #     return self._parse_relationship_ce(yaml_ce, key)

    # def _parse_oclass_ce(self, yaml_ce):
    #     """Parse the class expression referring to an ontology class.

    #     :param yaml_ce: The name of the ontology class
    #     :type yaml_ce: str
    #     :raises ValueError: Invalid class expression
    #     :return: The ontology class with the given name
    #     :rtype: OntologyClass
    #     """
    #     namespace, class_name = self.split_name(yaml_ce)
    #     x = self._namespace_registry[namespace][class_name]
    #     if not isinstance(x, OntologyClass):
    #         raise ValueError("Invalid class expression %s" % x)
    #     return x

    # def _parse_operator_ce(self, yaml_ce, operator):
    #     """Parse the class expression of an operator

    #     :param yaml_ce: The yaml definition of the class expression
    #     :type yaml_ce: Dict
    #     :param operator: The operator
    #     :type operator: str
    #     :return: The parsed class expression
    #     :rtype: OperatorClassExpression
    #     """
    #     operands = yaml_ce[operator]
    #     if not isinstance(operands, list):
    #         operands = [operands]
    #     parsed_operands = list()
    #     for operand in operands:
    #         parsed_operands.append(
    #             self._parse_class_expression(operand)
    #         )
    #     return OperatorClassExpression(operator.lower(), parsed_operands)

    # def _parse_relationship_ce(self, yaml_ce, rel_key):
    #     """Parse the class expression containing statements on
    #     the relationships an individual can have

    #     :param yaml_ce: The yaml definition of the class expression
    #     :type yaml_ce: Dict
    #     :param rel_key: The relationship
    #     :type rel_key: str
    #     :return: The parsed class expression
    #     :rtype: RelationshipClassExpression
    #     """
    #     namespace, rel_name = self.split_name(rel_key)
    #     rel = self._namespace_registry[namespace][rel_name]
    #     if not isinstance(rel, OntologyRelationship):
    #         raise ValueError("Invalid relationship %s in class expression %s "
    #                          % (rel, yaml_ce))
    #     target = self._parse_class_expression(
    #         yaml_ce[rel_key][TARGET_KEY]
    #     )
    #     cardinality = yaml_ce[rel_key][CARDINALITY_KEY] \
    #         if CARDINALITY_KEY in yaml_ce[rel_key] else "many"
    #     exclusive = yaml_ce[rel_key][EXCLUSIVE_KEY] \
    #         if EXCLUSIVE_KEY in yaml_ce[rel_key] else False
    #     return RelationshipClassExpression(
    #         relationship=rel, range=target,
    #         cardinality=cardinality, exclusive=exclusive
    #     )

    # def _validate_parsed_datastructure(self, namespace):
    #     """Do some tests on the created datastructure

    #     :param namespace: The current namespace to test
    #     :type namespace: OntologyNamespace
    #     :raises RuntimeError: rel and inverse are both active
    #     :raises RuntimeError: rel and inverse are both passive
    #     """
    #     CUBA = self._namespace_registry.get_main_namespace()
    #     for entity in namespace:
    #         if isinstance(entity, OntologyRelationship):
    #             inverse = entity.inverse
    #             if (
    #                 entity.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP)
    #                 and inverse.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP)
    #             ):
    #                 raise RuntimeError(
    #                     "%s and its inverse %s are both active relationships!"
    #                     % (entity, inverse)
    #                 )
    #             if (
    #                 entity.is_subclass_of(CUBA.PASSIVE_RELATIONSHIP)
    #                 and inverse.is_subclass_of(CUBA.PASSIVE_RELATIONSHIP)
    #             ):
    #                 raise RuntimeError(
    #                     "%s and its inverse %s are both passive relationships!"
    #                     % (entity, inverse)
    #                 )
