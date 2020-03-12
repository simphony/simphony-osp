# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import yaml
import logging
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.class_expression.operator_ce import OPERATORS
from osp.core.ontology.class_expression import \
    OperatorClassExpression, RelationshipClassExpression
from osp.core.ontology.validator import validate

from osp.core.ontology.keywords import (
    ONTOLOGY_KEY, NAMESPACE_KEY,
    ROOT_RELATIONSHIP, ROOT_ATTRIBUTE, DESCRIPTION_KEY, SUPERCLASSES_KEY,
    INVERSE_KEY, DEFAULT_REL_KEY, DATATYPE_KEY, ATTRIBUTES_KEY, DISJOINTS_KEY,
    EQUIVALENT_TO_KEY, DOMAIN_KEY, RANGE_KEY, CHARACTERISTICS_KEY,
    CARDINALITY_KEY, TARGET_KEY, EXCLUSIVE_KEY, AUTHOR_KEY, VERSION_KEY
)

logger = logging.getLogger(__name__)


class Parser:
    """
    Class that parses a YAML file and finds information about the entities
    contained.
    """

    def __init__(self, installer=None):
        self._installer = installer
        if not installer:
            from osp.core import ONTOLOGY_INSTALLER
            self._installer = ONTOLOGY_INSTALLER
        self._namespace_registry = self._installer.namespace_registry

        self._filename = None
        self._yaml_doc = None
        self._ontology_namespace = None

    @staticmethod
    def get_filepath(filename):
        if not filename.endswith(".yml"):
            filename = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "yml", "ontology.%s.yml" % filename
            )
        return filename

    def parse(self, filename, osp_module=None):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        from osp.core.ontology.namespace import OntologyNamespace

        logger.info("Parsing file %s" % filename)
        self.__init__(self._installer)
        self._filename = self.get_filepath(filename)
        self._yaml_doc = self.get_yaml_doc(self._filename)
        self._installer.tmp_open(self._filename)
        validate(self._yaml_doc,
                 context="<%s>" % os.path.basename(self._filename))
        author = (self._yaml_doc[AUTHOR_KEY]
                  if AUTHOR_KEY in self._yaml_doc else None)
        self._ontology_namespace = OntologyNamespace(
            name=self._yaml_doc[NAMESPACE_KEY],
            author=author,
            version=self._yaml_doc[VERSION_KEY]
        )
        self._namespace_registry._add_namespace(self._ontology_namespace)
        self._parse_ontology()
        self._installer.set_module_attr(osp_module)
        return self._ontology_namespace

    @staticmethod
    def get_yaml_doc(file_path):
        """Parse the file path to yaml

        :param file_path: The path to the file to parse.
        :type file_path: str
        """
        with open(file_path, 'r') as stream:
            yaml_doc = yaml.safe_load(stream)
        return yaml_doc

    def _parse_ontology(self):
        """Parse the entity descriptions."""
        logger.debug("Parse the ontology %s" % self._ontology_namespace.name)
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]

        for entity_name in cuds_yaml_doc:
            self._load_entity(entity_name)

        missing_inverse = set()
        for entity in self._ontology_namespace:
            self._validate_entity(entity)
            self._load_class_expressions(entity)
            if isinstance(entity, OntologyClass):
                self._add_attributes(entity)
            elif isinstance(entity, OntologyRelationship):
                self._set_inverse(entity, missing_inverse)
                self._parse_rel_characteristics(entity)
                self._check_default_rel(entity)
            else:
                self._set_datatype(entity)
        for entity in missing_inverse:
            self._create_missing_inverse(entity)
        self._validate_parsed_datastructure(self._ontology_namespace)

    @staticmethod
    def split_name(name):
        try:
            a, b = name.split(".")
            return a, b
        except ValueError as e:
            raise ValueError("Reference to entity %s without namespace"
                             % name) from e

    def _load_entity(self, entity_name):
        """Load an entity into the registry

        :param entity_name: The name of the entity to load.
        :type entity_name: str
        """
        if entity_name in self._ontology_namespace:
            return

        logger.debug("Parse entity definition for %s" % entity_name)
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity_name]
        description = None
        if DESCRIPTION_KEY in entity_yaml_doc:
            description = entity_yaml_doc[DESCRIPTION_KEY]

        # load the superclasses first
        superclass_names = entity_yaml_doc[SUPERCLASSES_KEY]
        superclasses = list()
        for p in superclass_names:
            if not isinstance(p, str):
                continue
            namespace, superclass_name = self.split_name(p)
            namespace = self._namespace_registry[namespace]
            if namespace is self._ontology_namespace:
                self._load_entity(superclass_name)
            superclasses.append(namespace[superclass_name])
        entity = self._create_entity(entity_name, superclasses, description)
        self._ontology_namespace._add_entity(entity)
        for p in superclasses:
            p._add_subclass(entity)

    def _load_class_expressions(self, entity):
        """Load class expressions.

        :param entity_name: The name of the entity to load.
        :type entity_name: str
        """
        logger.debug("Parse class expressions for %s" % entity)
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        # The keywords containing the class expressions
        if isinstance(entity, OntologyClass):
            keywords = [SUPERCLASSES_KEY, EQUIVALENT_TO_KEY, DISJOINTS_KEY]
        elif isinstance(entity, OntologyRelationship):
            keywords = [DOMAIN_KEY, RANGE_KEY]
        else:
            return

        # Parse the class expression for each keyword
        for keyword in keywords:
            if keyword not in entity_yaml_doc:
                continue
            ce_yaml = entity_yaml_doc[keyword]
            if not isinstance(ce_yaml, list):
                ce_yaml = [ce_yaml]

            for ce in ce_yaml:
                entity._add_class_expression(
                    keyword, self._parse_class_expression(ce)
                )

    def _create_entity(self, entity_name, superclasses, description):
        """Create an entity object

        :param entity_name: The name of the entity
        :type entity_name: str
        :param description: The description of the entity
        :type yaml_def: str
        """
        superclass_names = {entity_name}
        for p in superclasses:
            superclass_names |= {x.name for x in p.superclasses}
        if ROOT_ATTRIBUTE in superclass_names:
            Class = OntologyAttribute
        elif ROOT_RELATIONSHIP in superclass_names:
            Class = OntologyRelationship
        else:
            Class = OntologyClass
        result = Class(namespace=self._ontology_namespace,
                       name=entity_name,
                       superclasses=superclasses,
                       description=description)
        self._ontology_namespace._add_entity(result)
        return result

    def _add_attributes(self, entity: OntologyClass):
        """Add a attribute to an ontology class

        :param entity: The ontology to add the attributes to
        :type entity: OntologyClass
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        attributes_def = None
        if ATTRIBUTES_KEY in entity_yaml_doc:
            attributes_def = entity_yaml_doc[ATTRIBUTES_KEY]

        if attributes_def is None:
            return

        # Add the attributes one by one
        for attribute_name, default in attributes_def.items():
            attribute_namespace, attribute_name = \
                self.split_name(attribute_name)
            attribute_namespace = self._namespace_registry[attribute_namespace]
            attribute = attribute_namespace[attribute_name]
            entity._add_attribute(attribute, default)

    def _set_inverse(self, entity: OntologyRelationship, missing_inverse: set):
        """Set the inverse of the given entity

        :param entity: The ontology relationship to set an inverse.
        :type entity: OntologyRelationship
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        # Check if incerse is defined
        inverse_def = None
        if INVERSE_KEY in entity_yaml_doc:
            inverse_def = entity_yaml_doc[INVERSE_KEY]
        if inverse_def is None:
            missing_inverse |= {entity}
            return

        # inverse is defined
        inverse_namespace, inverse_name = self.split_name(inverse_def)
        inverse_namespace = self._namespace_registry[inverse_namespace]
        inverse = inverse_namespace[inverse_name]
        if inverse.inverse and inverse.inverse != entity:
            raise RuntimeError(
                "Conflicting inverses for %s, %s, %s"
                % (entity, inverse, inverse.inverse)
            )
        entity._set_inverse(inverse)
        inverse._set_inverse(entity)
        if inverse in missing_inverse:
            missing_inverse.remove(inverse)
        self._set_missing_passive(entity)

    def _set_missing_passive(self, entity):
        CUBA = self._namespace_registry.get_main_namespace()
        if self._ontology_namespace == CUBA:
            return
        for x in [entity, entity.inverse]:
            if (
                CUBA.ACTIVE_RELATIONSHIP in x.direct_superclasses
            ):
                x.inverse._add_superclass(CUBA.PASSIVE_RELATIONSHIP)
                CUBA.PASSIVE_RELATIONSHIP._add_subclass(x.inverse)
            if (
                CUBA.PASSIVE_RELATIONSHIP in x.direct_superclasses
            ):
                x.inverse._add_superclass(CUBA.ACTIVE_RELATIONSHIP)
                CUBA.ACTIVE_RELATIONSHIP._add_subclass(x.inverse)

    def _create_missing_inverse(self, entity: OntologyRelationship):
        """Create the missing inverse for an relationship

        :param entity: the relationship to add the inverse to
        :type entity: OntologyRelationship
        :return: The added inverse
        :rtype: OntologyRelationship
        """
        if entity.inverse:  # inverse not missing. Return.
            return entity.inverse

        # Try to infer the superclasses of the inverse
        inverse_superclasses = list()
        for x in entity.direct_superclasses:
            if x.inverse:
                inverse_superclasses.append(x.inverse)
            elif x.namespace == self._ontology_namespace:
                inverse_superclasses.append(self._create_missing_inverse(x))
        if not inverse_superclasses:
            inverse_superclasses = [  # Fallback to CUBA.RELATIONSHIP
                self._namespace_registry.get_main_namespace().relationship
            ]

        # Create the inverse
        inverse = OntologyRelationship(
            namespace=self._ontology_namespace,
            name="INVERSE_OF_%s" % entity.name,
            superclasses=inverse_superclasses,
            description="Inverse of %s" % entity.name
        )
        for x in inverse_superclasses:
            x._add_subclass(inverse)
        self._ontology_namespace._add_entity(inverse)
        inverse._set_inverse(entity)  # set the inverses
        entity._set_inverse(inverse)
        return inverse

    def _check_default_rel(self, entity: OntologyRelationship):
        """Check of the given relationship the default
        When it is a default, save that accordingly.

        :param entity: The relationship to check
        :type entity: OntologyRelationship
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]
        if DEFAULT_REL_KEY in entity_yaml_doc \
                and entity_yaml_doc[DEFAULT_REL_KEY]:
            self._ontology_namespace._default_rel = entity

    def _set_datatype(self, entity: OntologyAttribute):
        """Set the datatype of a attribute

        :param entity: The attribute to set the datatype of
        :type entity: OntologyAttribute
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]

        datatype_def = None
        if DATATYPE_KEY in entity_yaml_doc:
            datatype_def = entity_yaml_doc[DATATYPE_KEY]

        if datatype_def is not None:
            entity._set_datatype(datatype_def)

    def _validate_entity(self, entity):
        """Validate the yaml definition of an entity.
        Will check for the special keywords of the different entity types.

        :param entity: The entity to check.
        :type entity: OntologyEntity
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]
        if isinstance(entity, OntologyClass):
            pattern = "class_def"
        elif isinstance(entity, OntologyRelationship):
            pattern = "relationship_def"
        else:
            pattern = "attribute_def"

        validate(
            entity_yaml_doc, pattern,
            context="<%s>/ONTOLOGY/%s" % (os.path.basename(self._filename),
                                          entity.name)
        )

    def _parse_rel_characteristics(self, entity):
        """Parse the characteristics of a relationship

        :param entity: The relationship to parse the characteristics for.
        :type entity: OntologyRelationship
        """
        cuds_yaml_doc = self._yaml_doc[ONTOLOGY_KEY]
        entity_yaml_doc = cuds_yaml_doc[entity.name]
        if CHARACTERISTICS_KEY not in entity_yaml_doc:
            return
        characteristics = entity_yaml_doc[CHARACTERISTICS_KEY]
        for c in characteristics:
            entity._add_characteristic(c)

    def _parse_class_expression(self, yaml_ce):
        """Recursively parse a class expression in yaml format.

        :param yaml_ce: The yaml expression to parse
        :type yaml_ce: Union[str, Dict, List]
        :raises ValueError: Invalid expression
        :return: The parsed class expression.
        :rtype: ClassExpression
        """
        logger.debug("Parse class expression %s" % yaml_ce)
        if isinstance(yaml_ce, str):
            return self._parse_oclass_ce(yaml_ce)

        if isinstance(yaml_ce, dict) and len(yaml_ce) != 1:
            raise ValueError(
                "Invalid dictionary call expression: %s. "
                "A class expression that is a dictionary is only allowed to "
                "have at most one key. You should probably transform it to a "
                "list of dictionaries." % yaml_ce
            )
        key = next(iter(yaml_ce.keys()))
        if key.lower() in OPERATORS:
            return self._parse_operator_ce(yaml_ce, key)
        return self._parse_relationship_ce(yaml_ce, key)

    def _parse_oclass_ce(self, yaml_ce):
        """Parse the class expression referring to an ontology class.

        :param yaml_ce: The name of the ontology class
        :type yaml_ce: str
        :raises ValueError: Invalid class expression
        :return: The ontology class with the given name
        :rtype: OntologyClass
        """
        namespace, class_name = self.split_name(yaml_ce)
        x = self._namespace_registry[namespace][class_name]
        if not isinstance(x, OntologyClass):
            raise ValueError("Invalid class expression %s" % x)
        return x

    def _parse_operator_ce(self, yaml_ce, operator):
        """Parse the class expression of an operator

        :param yaml_ce: The yaml definition of the class expression
        :type yaml_ce: Dict
        :param operator: The operator
        :type operator: str
        :return: The parsed class expression
        :rtype: OperatorClassExpression
        """
        operands = yaml_ce[operator]
        if not isinstance(operands, list):
            operands = [operands]
        parsed_operands = list()
        for operand in operands:
            parsed_operands.append(
                self._parse_class_expression(operand)
            )
        return OperatorClassExpression(operator.lower(), parsed_operands)

    def _parse_relationship_ce(self, yaml_ce, rel_key):
        """Parse the class expression containing statements on
        the relationships an individual can have

        :param yaml_ce: The yaml definition of the class expression
        :type yaml_ce: Dict
        :param rel_key: The relationship
        :type rel_key: str
        :return: The parsed class expression
        :rtype: RelationshipClassExpression
        """
        namespace, rel_name = self.split_name(rel_key)
        rel = self._namespace_registry[namespace][rel_name]
        if not isinstance(rel, OntologyRelationship):
            raise ValueError("Invalid relationship %s in class expression %s "
                             % (rel, yaml_ce))
        target = self._parse_class_expression(
            yaml_ce[rel_key][TARGET_KEY]
        )
        cardinality = yaml_ce[rel_key][CARDINALITY_KEY] \
            if CARDINALITY_KEY in yaml_ce[rel_key] else "many"
        exclusive = yaml_ce[rel_key][EXCLUSIVE_KEY] \
            if EXCLUSIVE_KEY in yaml_ce[rel_key] else False
        return RelationshipClassExpression(
            relationship=rel, range=target,
            cardinality=cardinality, exclusive=exclusive
        )

    def _validate_parsed_datastructure(self, namespace):
        """Do some tests on the created datastructure

        :param namespace: The current namespace to test
        :type namespace: OntologyNamespace
        :raises RuntimeError: rel and inverse are both active
        :raises RuntimeError: rel and inverse are both passive
        """
        CUBA = self._namespace_registry.get_main_namespace()
        for entity in namespace:
            if isinstance(entity, OntologyRelationship):
                inverse = entity.inverse
                if (
                    entity.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP)
                    and inverse.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP)
                ):
                    raise RuntimeError(
                        "%s and its inverse %s are both active relationships!"
                        % (entity, inverse)
                    )
                if (
                    entity.is_subclass_of(CUBA.PASSIVE_RELATIONSHIP)
                    and inverse.is_subclass_of(CUBA.PASSIVE_RELATIONSHIP)
                ):
                    raise RuntimeError(
                        "%s and its inverse %s are both passive relationships!"
                        % (entity, inverse)
                    )
