# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


class ValidityChecker():
    """Class that checks the validity of an ontology during
    the installation process"""

    def __init__(self, parser, class_generator):
        """Constructor.

        :param parser: The parser used for parsing the yml file.
        :type parser: Parser
        :param class_generator: The class generator.
        :type class_generator: ClassGenerator
        """
        self.parser = parser
        self.class_generator = class_generator
        self.root_rel = class_generator.ROOT_RELATIONSHIP
        self.root_active = class_generator.ROOT_ACTIVE_RELATIONSHIP
        self.root_passive = class_generator.ROOT_PASSIVE_RELATIONSHIP
        self.root_non_class = class_generator.ROOT_NOT_CLASSES
        self.attr_inverse = class_generator.INVERSE_ATTRIBUTE_KEY
        self.attr_parent = parser.PARENT_ATTRIBUTE_KEY
        self.attr_def = parser.DEFINITION_ATTRIBUTE_KEY

    def repair(self):
        """Check for repairable ontology problems and repair them"""
        self._add_missing_inverse_relationships(self.parser)

    def check_validity(self):
        """Check if the ontology satisfies certain constraints"""
        self._check_obligatory_classes(self.parser)
        self._check_inverses(self.parser)
        self._check_attributes(self.parser)

    def _add_missing_inverse_relationships(self, parser):
        """
        If class A, can have relationship rel with class B as object,
        class B must be able to connect to class A with relationship rel^-1.
        """
        # iterate over all relationships and add inverse, if missing
        for entity in parser._entities:
            # subject must not be a relationship
            if self.root_rel in parser.get_ancestors(entity):
                continue
            for key in set(parser._ontology[entity].keys()):
                # check if predicate is relationship
                if (
                    not key.startswith("CUBA.")
                    or self.root_rel not in parser.get_ancestors(
                        key[5:])
                ):
                    continue
                targets = parser.get_value(entity, key).keys()
                for target in targets:
                    # object must not be relationship
                    if (
                        not target.startswith("CUBA.")
                        or self.root_rel in parser.get_ancestors(
                            target[5:])
                    ):
                        continue
                    parser._add_inverse(target[5:], key[5:], entity)

    def _check_obligatory_classes(self, parser):
        """Check if certain obligatory classes are present in the ontology

        :param parser: The parser object.
        :type parser: Parser
        """
        entities = parser.get_entities()
        msg1 = "Missing obligatory cuds class in ontology."
        assert self.root_rel in entities, msg1
        assert self.root_active in entities, msg1
        assert self.root_passive in entities, msg1
        assert self.root_rel in parser.get_ancestors(self.root_active)
        assert self.root_rel in parser.get_ancestors(self.root_passive)
        for entity in set(entities) - {self.root_rel,
                                       self.root_active, self.root_passive}:
            ancestors = set(parser.get_ancestors(entity))
            typ = {self.root_active, self.root_passive} & ancestors
            if self.root_rel in ancestors:
                assert len(typ) == 1, "Relationship must be active xor passive"

    def _check_inverses(self, parser):
        """Check if the inverses of the relationships are present and valid

        :param parser: The parser object
        :type parser: Parser
        """
        assert parser.get_value(self.root_active, self.attr_inverse) == \
            "CUBA." + self.root_passive
        assert parser.get_value(self.root_passive, self.attr_inverse) == \
            "CUBA." + self.root_active
        entities = parser.get_entities()
        for entity in set(entities) - {self.root_rel,
                                       self.root_active, self.root_passive}:
            ancestors = set(parser.get_ancestors(entity))
            if self.root_rel not in ancestors:
                continue
            typ = {self.root_active, self.root_passive} & ancestors
            inverse = parser.get_value(entity, self.attr_inverse)
            assert inverse.startswith("CUBA.")
            inverse_ancestors = set(parser.get_ancestors(inverse[5:]))
            inverse_type = {self.root_active,
                            self.root_passive} & inverse_ancestors
            assert typ | inverse_type == {self.root_active,
                                          self.root_passive}, \
                "Inverse of active relationship must be passive and vice-versa"
            assert parser.get_value(inverse[5:], self.attr_inverse) == \
                "CUBA.%s" % entity, "Inverse of inverse must be identity"

    def _check_attributes(self, parser):
        """Check if the attributes of an entity are valid.

        :param parser: The parser object.
        :type parser: Parser.
        """
        for entity in parser.get_entities():
            for attribute in parser.get_own_attributes(entity):
                if attribute in map(str.lower, [self.attr_def,
                                                self.attr_parent]):
                    continue
                try:
                    ancestors = set(parser.get_ancestors(attribute.upper()))
                except KeyError as e:
                    raise AssertionError("Unknown cuba key CUBA.%s specified!"
                                         % attribute.upper()) from e
                assert len({self.root_non_class,
                            self.root_rel} & ancestors) == 1, (
                    "Attribute %s not allowed for %s. "
                    "Must be a relationship xor a value."
                    % (attribute, entity))
                if self.root_rel in ancestors:
                    for target in parser.get_value(
                            entity, "CUBA." + attribute.upper()):
                        assert target.startswith("CUBA."), \
                            "Target of a relationship must be a cuba key."
                        try:
                            parser.get_ancestors(target[5:])
                        except KeyError as e:
                            raise AssertionError(
                                "Unknown cuba key %s specified!" % target) \
                                from e
