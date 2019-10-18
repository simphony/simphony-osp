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
        self.root_non_class = class_generator.ROOT_NOT_CLASSES
        self.attr_inverse = class_generator.INVERSE_ATTRIBUTE_KEY
        self.attr_superclass = parser.SUPERCLASS_ATTRIBUTE_KEY
        self.attr_def = parser.DEFINITION_ATTRIBUTE_KEY
        self.attr_default_rel = class_generator.DEFAULT_REL_ATTRIBUTE_KEY
        self.default_relationship = None

    def check_and_repair(self):
        """Check if the ontology satisfies certain constraints"""
        self._check_obligatory_classes(self.parser)
        self._check_inverses(self.parser)
        self._check_attributes(self.parser)
        self._add_missing_inverse_relationships(self.parser)
        # self._check_cycles(self.parser)

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
        msg1 = "Missing obligatory cuds class in ontology: "
        assert self.root_rel in entities, msg1 + self.root_rel
        assert self.root_active in entities, msg1 + self.root_active
        assert self.root_rel in parser.get_ancestors(self.root_active)
        for entity in set(entities) - {self.root_rel,
                                       self.root_active}:
            try:
                if parser.get_value(entity, "default_rel"):
                    assert not self.default_relationship, \
                        "Only one default relationship allowed!"
                    self.default_relationship = entity
            except KeyError:
                pass
        self.default_relationship = self.default_relationship or \
            "ACTIVE_RELATIONSHIP"
        assert (
            len([e for e in entities
                 if parser.get_value(
                     e, self.attr_superclass) is None]) == 1), \
            "The ontology must have exactly one root"

    def _check_inverses(self, parser):
        """Check if the inverses of the relationships are present and valid

        :param parser: The parser object
        :type parser: Parser
        """
        # check inverse of ActiveRelationship
        assert parser.get_value(self.root_active, self.attr_inverse) != \
            "CUBA." + self.root_active, \
            "Inverse of %s must not be %s" % (
                self.root_active, self.root_active)

        # Check inverse of the other relationships
        entities = parser.get_entities()
        for entity in set(entities) - {self.root_rel,
                                       self.root_active}:
            ancestors = set(parser.get_ancestors(entity))
            if self.root_rel not in ancestors:
                continue
            is_active = self.root_active in ancestors
            inverse = parser.get_value(entity, self.attr_inverse)
            assert inverse.startswith("CUBA."), \
                "Invalid inverse of %s" % entity
            inverse_ancestors = set(parser.get_ancestors(inverse[5:]))
            inverse_is_active = self.root_active in inverse_ancestors
            assert not (is_active and inverse_is_active), \
                "The inverse of an active relationship must not be active"
            assert parser.get_value(inverse[5:], self.attr_inverse) == \
                "CUBA.%s" % entity, "Inverse of inverse must be identity: %s" \
                % entity

    def _check_attributes(self, parser):
        """Check if the attributes of an entity are valid.

        :param parser: The parser object.
        :type parser: Parser.
        """
        for entity in set(parser.get_entities()):
            for attribute in parser.get_cuba_attributes_filtering(entity, []):
                attribute = attribute[5:]
                if attribute in map(str.lower, [self.attr_def,
                                                self.attr_superclass,
                                                self.root_non_class,
                                                self.attr_default_rel]):
                    continue
                # Check for unknown Cuba Key
                try:
                    ancestors = set(parser.get_ancestors(attribute.upper()))
                except KeyError as e:
                    raise KeyError("Unknown cuba key CUBA.%s specified!"
                                   % attribute.upper()) from e
                # check type
                if not len({self.root_non_class,
                            self.root_rel}
                           & (ancestors | {attribute.upper()})) == 1:
                    print("> ", attribute)
                    target = parser.get_value(entity, "CUBA." + attribute)
                    parser.update_attribute(
                        entity,
                        "CUBA." + self.default_relationship,
                        {"CUBA." + attribute: target})
                    parser.del_attribute(entity, "CUBA." + attribute)
                    attribute = self.default_relationship
                    ancestors = parser.get_ancestors(self.default_relationship)

                # check relationship target
                if self.root_rel in ancestors:
                    for target, target_dict in parser.get_value(
                            entity, "CUBA." + attribute.upper()).items():
                        assert target.startswith("CUBA."), \
                            "Target of a relationship must be a cuba key."
                        allowed_target_dict_keys = {"cardinality",
                                                    "scope",
                                                    "range", "shape"}
                        assert target_dict is None or \
                            target_dict.keys() \
                            - allowed_target_dict_keys == set(), \
                            "Specifying %s not allowed for relationship %s" % (
                                target_dict.keys() - allowed_target_dict_keys,
                                (attribute, target))
                        try:
                            parser.get_ancestors(target[5:])
                        except KeyError as e:
                            raise AssertionError(
                                "Unknown cuba key %s specified!" % target) \
                                from e

    def _get_non_cyclic_relationships(self, parser):
        """Get the relationships that do not allow cycles.

        :param parser: The parser that parsed the yaml file.
        :type parser: Parser
        :return: The relationships that do not allow cycles.
        :rtype: bool
        """
        non_cyclic_relationships = set()
        for entity in parser.get_entities():
            # only consider active relationships
            ancestors = set(parser.get_ancestors(entity)) | {entity}
            is_active = self.root_active in ancestors
            allow_cycles = None
            # also check ancestors for allow_cycles attribute
            for ancestor in ancestors:
                try:
                    allow = parser.get_value(ancestor, "allow_cycles")
                    assert allow_cycles is None, \
                        "Overwrite of allow_cycles is not allowed"
                    assert is_active, \
                        "allow_cycles only allowed for active relationships"
                    allow_cycles = allow
                except KeyError:
                    continue
            if not allow_cycles and is_active:
                non_cyclic_relationships.add(entity)
        return non_cyclic_relationships

    # def _check_cycles(self, parser):
    #     """Check if the ontology contains cycles that are not allowed.

    #     :param parser: The parser that parsed the yaml file
    #     :type parser: Parser
    #     """
    #     non_cyclic_relationships = self._get_non_cyclic_relationships(parser)
    #     visited = set()
    #     rec_stack = list()

    #     # check for each entity if its part of a cycle
    #     for entity in parser.get_entities() - {self.root_rel,
    #                                            self.root_active}:
    #         # only consider real entities
    #         ancestors = set(parser.get_ancestors(entity))
    #         if not {self.root_rel, self.root_non_class} & ancestors:
    #             if entity not in visited:
    #                 assert not self._is_cyclic(parser=parser,
    #                                            entity=entity,
    #                                            rels=non_cyclic_relationships,
    #                                            visited=visited,
    #                                            rec_stack=rec_stack), (
    #                     "Cycles only allowed for active relationships "
    #                     "with attribute allow_cycles=true. Stack: %s" %
    #                     rec_stack)

    # def _is_cyclic(self, parser, entity, rels, visited, rec_stack):
    #     """Recursively check if the subgraph rooted in the
    #     given entity contains cycles.

    #     :param parser: The parser object that parsed the yaml file.
    #     :type parser: Parser
    #     :param entity: The entity to start the search for cycles.
    #     :type entity: str
    #     :param rels: The relationships to consider.
    #     :type rels: Set[str]
    #     :param visited: The CUDS entities already visited
    #     :type visited: Set[str]
    #     :param rec_stack: The recursive stack. Used to detect the cycles.
    #     :type rec_stack: List[str]
    #     :return: Whether a cycles has been detected
    #     :rtype: bool
    #     """
    #     visited.add(entity)
    #     rec_stack.append(entity)

    #     # also consider inherited relationships = rels of ancestors
    #     for anc in set(self.parser.get_ancestors(entity)) | {entity}:
    #         for rel in self.parser.get_cuba_attributes_filtering(anc, []):
    #             rel = rel[5:]
    #             # skip passive rels / entities / rels which allow cycles
    #             if rel not in rels:
    #                 continue
    #             # Check neighbours recursively
    #             for neighbour in parser.get_value(anc, "CUBA." + rel).keys():
    #                 neighbour = neighbour[5:]

    #                 if neighbour not in visited:  # recurse
    #                     if self._is_cyclic(parser=parser,
    #                                        entity=neighbour,
    #                                        rels=rels,
    #                                        visited=visited,
    #                                        rec_stack=rec_stack):
    #                         return True
    #                 elif neighbour in rec_stack:  # cycle detected
    #                     rec_stack.append("<rel: %s>" % rel)
    #                     rec_stack.append(neighbour)
    #                     return True
    #     # remove from call stack
    #     assert rec_stack.pop() == entity
    #     return False
