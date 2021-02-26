"""Test the API with the EMMO ontology."""

import itertools
import unittest2 as unittest
import rdflib
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.oclass_restriction import Restriction, QUANTIFIER, RTYPE
from osp.core.ontology.oclass_composition import Composition


try:
    from osp.core.namespaces import math
    from osp.core.namespaces import materials
    from osp.core.namespaces import siunits
except ImportError:  # When the EMMO ontology is not installed.
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("emmo")
    _namespace_registry.update_namespaces()
    math = _namespace_registry.math
    materials = _namespace_registry.materials
    siunits = _namespace_registry.siunits


# Mappings from OWL objects and ontology classes to enums used
# in oclass_composition.py.
quantifier_owl_to_enum = {rdflib.OWL.someValuesFrom: QUANTIFIER.SOME,
                          rdflib.OWL.allValuesFrom: QUANTIFIER.ONLY,
                          rdflib.OWL.cardinality: QUANTIFIER.EXACTLY,
                          rdflib.OWL.minCardinality: QUANTIFIER.MIN,
                          rdflib.OWL.maxCardinality: QUANTIFIER.MAX,
                          rdflib.OWL.hasValue: QUANTIFIER.VALUE}
rtypes = {OntologyRelationship: RTYPE.RELATIONSHIP_RESTRICTION,
          OntologyAttribute: RTYPE.ATTRIBUTE_RESTRICTION}


class TestRestrictionsEmmo(unittest.TestCase):
    """Test the restrictions in EMMO ontology (class vs blank node).

    In this set of tests, the information that the restrictions yield is
    compared against information constructed from the blank node attached to
    each restriction.
    """

    emmo_classes = (math.Integer, math.Real, math.Boolean, math.Vector,
                    math.Matrix, materials.Nucleus, materials.ElectronCloud,
                    siunits.Gray, siunits.Watt)

    def iter_restrictions(self):
        """Iterates over all the restrictions present in the test classes."""
        restrictions = iter([])
        for datatype in self.emmo_classes:
            restrictions = itertools.chain(restrictions,
                                           (r for r in datatype.axioms
                                            if type(r) is Restriction))
        return restrictions

    # def test__str(self):
    #    This test is left for the test case TestSpecificRestrictionsEmmo.

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

    def test_quantifier(self):
        """Test the quantifier method.

        Also tests _compute_target and _check_quantifier implicitly.
        """
        for r in self.iter_restrictions():
            b_node = r._bnode
            graph = r._graph

            restriction_predicates = graph.predicates(subject=b_node)
            quantifiers = [quantifier_owl_to_enum[p]
                           for p in restriction_predicates
                           if p in quantifier_owl_to_enum]
            self.assertEqual(len(quantifiers), 1, "The restriction has not "
                                                  "exactly one quantifier.")
            quantifier = quantifiers[0]
            self.assertIs(quantifier, r.quantifier)

    def test_target(self):
        """Test the target method.

        Also tests _compute_target and _check_quantifier implicitly.
        """
        quantifiers_reverse = {item: key for key, item
                               in quantifier_owl_to_enum.items()}

        for r in self.iter_restrictions():
            b_node = r._bnode
            graph = r._graph

            restriction_predicates = graph.predicates(subject=b_node)
            quantifiers = [quantifier_owl_to_enum[p]
                           for p in restriction_predicates
                           if p in quantifier_owl_to_enum]
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
            restriction_type = rtypes[type(prop)]
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


class TestSpecificRestrictionsEmmo(unittest.TestCase):
    """Test the restrictions in EMMO ontology (definition vs class).

    In this test, two restrictions for the EMMO ontology class Integer are
    constructed from scratch, and the resulting restriction object is compared
    against the data used to build it.
    """

    def __init__(self, *args, **kwargs):
        """Instantiation of the restrictions used in the test."""
        super().__init__(*args, **kwargs)

        self.restriction_data = []
        # See the documentation of the method 'build_restriction' on how to
        # specify the source data from which restrictions are instantiated.

        # Specific case 1:
        #    math.hasNumericalData QUANTIFIER.SOME
        #    http://www.w3.org/2001/XMLSchema#integer
        self.restriction_data += [{'string': 'math.hasNumericalData '
                                             'QUANTIFIER.SOME '
                                             'http://www.w3.org/2001/XMLSchema'
                                             '#integer',
                                   'property': rdflib.URIRef('http://emmo.info'
                                                             '/emmo/middle'
                                                             '/math'
                                                             '#EMMO_faf79f53_'
                                                             '749d_40b2_807c'
                                                             '_d34244c192f4'),
                                   'quantifier': rdflib.OWL.someValuesFrom,
                                   'target': rdflib.URIRef('http://www.w3.org/'
                                                           '2001'
                                                           '/XMLSchema#integer'
                                                           )}
                                  ]

        # Specific case 2:
        #    mereotopology.hasProperPart QUANTIFIER.ONLY
        #    (OPERATOR.NOT math.Mathematical)'
        class PlaceholderComposition(rdflib.BNode):
            """Emulates the string representation of the Composition class.

            The point of this placeholder is to avoid the presence of the
            Composition class in this test, which only targets restrictions.
            """

            def __str__(self):
                return '(OPERATOR.NOT math.Mathematical)'

        self.restriction_data += [{'string': 'mereotopology.hasProperPart '
                                             'QUANTIFIER.ONLY (OPERATOR.NOT '
                                             'math.Mathematical)',
                                   'property': rdflib.URIRef('http://emmo.info'
                                                             '/emmo/top/'
                                                             'mereotopology'
                                                             '#EMMO_9380ab64_'
                                                             '0363_4804_b13f_'
                                                             '3a8a94119a76'),
                                   'quantifier': rdflib.OWL.allValuesFrom,
                                   'target': PlaceholderComposition()}
                                  ]

        self.restrictions = [self.build_restriction(data)
                             for data in self.restriction_data]

    @staticmethod
    def build_restriction(data):
        """Returns a Restriction object from a dictionary.

        Args:
            data (dict): The source dictionary. It is expected to have
            the following structure.
                {'string' (str): The string representation of the restriction,
                 'property' (rdflib.URIRef): The property affected by the
                                             restriction,
                 'quantifier' (rdflib.URIRef): One of the quantifiers defined
                                               by the OWL ontology,
                'target' (Union[rdflib.URIRef, rdflib.BNode]): Target of the
                                                          restriction,
                }
        """
        namespace_registry = math._namespace_registry
        graph = math._graph

        bnode = rdflib.BNode()
        graph.add((bnode, rdflib.RDF.type, rdflib.OWL.Restriction))
        graph.add((bnode, rdflib.OWL.onProperty, data['property']))
        graph.add((bnode, data['quantifier'], data['target']))
        restriction = Restriction(bnode, namespace_registry)

        return restriction

    def test___str__(self):
        """Tests the string representation of the restriction."""
        for data, restriction in zip(self.restriction_data, self.restrictions):
            self.assertEqual(data['string'], restriction.__str__(),
                             f'The string representation of the restriction'
                             f'does not match the expected one:'
                             f' {data["string"]}.')

    def test__property(self):
        """Test the _property method.

        Also tests _compute_property implicitly.
        """
        namespace_registry = math._namespace_registry
        for data, restriction in zip(self.restriction_data, self.restrictions):
            data_property = namespace_registry.from_iri(data['property'])
            self.assertEqual(data_property, restriction._property)

    def test_quantifier(self):
        """Test the quantifier method.

        Also tests _compute_target and _check_quantifier implicitly.
        """
        for data, restriction in zip(self.restriction_data, self.restrictions):
            quantifier = quantifier_owl_to_enum[data['quantifier']]
            self.assertIs(quantifier, restriction.quantifier)

    def test_target(self):
        """Test the target method.

        Also tests _compute_target and _check_quantifier implicitly.
        """
        for data, restriction in zip(self.restriction_data, self.restrictions):
            target_id = data['target']
            if isinstance(restriction.target, rdflib.term.Identifier):
                target_id_restriction = restriction.target
            elif isinstance(restriction.target, OntologyEntity):
                target_id_restriction = restriction.target.iri
            elif isinstance(restriction.target, Composition):
                target_id_restriction = restriction.target._bnode
            else:
                raise Exception(f"Unit test is incomplete, target of type "
                                f"{type(restriction.target)} not considered.")
            self.assertEqual(target_id, target_id_restriction)

    def test_rtype(self):
        """Test the rtype method.

        Also tests _compute_rtype implicitly.
        """
        namespace_registry = math._namespace_registry
        for data, restriction in zip(self.restriction_data, self.restrictions):
            data_property = namespace_registry.from_iri(data['property'])
            data_property_type = type(data_property)
            self.assertIs(rtypes[data_property_type], restriction.rtype)

    def test_attribute_and_relationship(self):
        """Tests both the relationship and the attribute method*.

        Make sure that the __init__ method of this class instantiates at least
        one example of a restriction on a relationship and on an attribute so
        that all cases are covered.
        """
        namespace_registry = math._namespace_registry
        for data, restriction in zip(self.restriction_data, self.restrictions):
            data_property = namespace_registry.from_iri(data['property'])
            class_data_property = type(data_property)
            if rtypes[class_data_property] == RTYPE.RELATIONSHIP_RESTRICTION:
                self.assertRaises(AttributeError, getattr,
                                  restriction, "attribute")
            elif rtypes[class_data_property] == RTYPE.ATTRIBUTE_RESTRICTION:
                self.assertRaises(AttributeError, getattr,
                                  restriction, "relationship")
            else:
                raise Exception(f"Incomplete test, restrictions of type "
                                f"{restriction.rtype} are not considered.")


if __name__ == "__main__":
    unittest.main()
