"""Test the API with the EMMO ontology."""

import unittest2 as unittest
import rdflib
import itertools
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.oclass_restriction import Restriction, QUANTIFIER, RTYPE
from osp.core.ontology.oclass_composition import Composition


try:
    from osp.core.namespaces import math
except ImportError:  # When the EMMO ontology is not installed.
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("emmo")
    _namespace_registry.update_namespaces()
    math = _namespace_registry.math


class TestRestrictionsEmmo(unittest.TestCase):
    """Test the restrictions in EMMO ontology."""

    emmo_datatypes = (math.Integer, math.Real, math.Boolean, math.Vector,
                      math.Matrix)

    quantifiers = {rdflib.OWL.someValuesFrom: QUANTIFIER.SOME,
                   rdflib.OWL.allValuesFrom: QUANTIFIER.ONLY,
                   rdflib.OWL.cardinality: QUANTIFIER.EXACTLY,
                   rdflib.OWL.minCardinality: QUANTIFIER.MIN,
                   rdflib.OWL.maxCardinality: QUANTIFIER.MAX}

    rtypes = {OntologyRelationship: RTYPE.RELATIONSHIP_RESTRICTION,
              OntologyAttribute: RTYPE.ATTRIBUTE_RESTRICTION}

    def iter_restrictions(self):
        """Returns all the datatypes of the test wrapped in an iterator."""
        restrictions = iter([])
        for datatype in self.emmo_datatypes:
            restrictions = itertools.chain(restrictions,
                                           (r for r in datatype.axioms
                                            if type(r) is Restriction))
        return restrictions

    def test___str__(self):
        """Test the __str__ method."""
        for r in self.iter_restrictions():
            self.assertIs(type(r.__str__()), str)

    def test_quantifier(self):
        """Test the quantifier method.

        Also tests _compute_target and _check_quantifier implicitly.
        """
        for r in self.iter_restrictions():
            b_node = r._bnode
            graph = r._graph

            restriction_predicates = graph.predicates(subject=b_node)
            quantifiers = [self.quantifiers[p] for p in restriction_predicates
                           if p in self.quantifiers]
            self.assertTrue(len(quantifiers) == 1, "The restriction has not "
                                                   "exactly one quantifier.")
            quantifier = quantifiers[0]
            self.assertIs(quantifier, r.quantifier)

    def test_target(self):
        """Test the target method.

        Also tests _compute_target and _check_quantifier implicitly.
        """
        quantifiers_reverse = {item: key for key, item
                               in self.quantifiers.items()}

        for r in self.iter_restrictions():
            b_node = r._bnode
            graph = r._graph

            restriction_predicates = graph.predicates(subject=b_node)
            quantifiers = [self.quantifiers[p] for p in restriction_predicates
                           if p in self.quantifiers]
            self.assertTrue(len(quantifiers) == 1, "The restriction has not "
                                                   " one quantifier.")
            quantifier = quantifiers[0]
            self.assertTrue(len(quantifiers) == 1, "The restriction has not "
                                                   "exactly one quantifier.")
            targets = graph.objects(subject=b_node,
                                    predicate=quantifiers_reverse[quantifier])
            targets = list(targets)
            self.assertTrue(len(targets) == 1, "The restriction has not "
                                               "exactly one target.")
            target_id = targets[0]
            if isinstance(r.target, rdflib.term.Identifier):
                target_id_restriction = r.target
            elif isinstance(r.target, OntologyEntity):
                target_id_restriction = r.target.iri
            elif isinstance(r.target, Composition):
                target_id_restriction = r.target._bnode
            else:
                raise Exception(f"Unit test is incomplete, target of type "
                                f"{type(r.target)} not considered.")
            self.assertEqual(target_id, target_id_restriction)

    def test__property(self):
        """Test the _property method.

        Also tests _compute_property implicitly.
        """
        for r in self.iter_restrictions():
            b_node = r._bnode
            graph = r._graph
            namespace_registry = r._namespace_registry

            properties = graph.objects(subject=b_node,
                                       predicate=rdflib.OWL.onProperty)
            properties = list(properties)
            self.assertTrue(len(properties) == 1, "The restriction refers not "
                                                  "exactly to one property.")
            prop = namespace_registry.from_iri(properties[0])
            self.assertEqual(prop, r._property)

    def test_rtype(self):
        """Test the rtype method.

        Also tests _compute_rtype implicitly.
        """
        for r in self.iter_restrictions():
            b_node = r._bnode
            graph = r._graph
            namespace_registry = r._namespace_registry

            properties = graph.objects(subject=b_node,
                                       predicate=rdflib.OWL.onProperty)
            properties = list(properties)
            self.assertTrue(len(properties) == 1, "The restriction refers not "
                                                  "exactly to one property.")
            prop = namespace_registry.from_iri(properties[0])
            restriction_type = self.rtypes[type(prop)]
            self.assertIs(restriction_type, r.rtype)

    def test_attribute_and_relationship(self):
        """Tests both the relationship and the attribute method*.

        *Only if both relationships and attributes are included in the
        restrictions of the EMMO datatypes to test).
        """
        for r in self.iter_restrictions():
            if r.rtype == RTYPE.RELATIONSHIP_RESTRICTION:
                self.assertRaises(AttributeError, getattr, r, "attribute")
            elif r.rtype == RTYPE.ATTRIBUTE_RESTRICTION:
                self.assertRaises(AttributeError, getattr, r, "relationship")
            else:
                raise Exception(f"Incomplete test, restrictions of type "
                                f"{r.rtype} are not considered.")


if __name__ == "__main__":
    unittest.main()
