"""Test the API with the EMMO ontology."""

import unittest2 as unittest
import rdflib
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.oclass_restriction import Restriction
from osp.core.ontology.oclass_composition import Composition, OPERATOR


try:
    from osp.core.namespaces import math
except ImportError:  # When the EMMO ontology is not installed.
    from osp.core.ontology import Parser
    Parser().parse("emmo")
    from osp.core.namespaces import math


predicate_to_operator = {rdflib.OWL.unionOf: OPERATOR.OR,
                         rdflib.OWL.intersectionOf: OPERATOR.AND,
                         rdflib.OWL.complementOf: OPERATOR.NOT}


class TestCompositionsEMMO(unittest.TestCase):
    """Test some composition examples taken from the EMMO ontology."""

    def __init__(self, *args, **kwargs):
        """Instantiation of the compositions used in the test."""
        super().__init__(*args, **kwargs)

        self.composition_data = []

        # Example 1:
        #   (math.Mathematical OPERATOR.AND perceptual.Symbol)
        self.composition_data += [{'string': '(math.Mathematical OPERATOR.AND'
                                             ' perceptual.Symbol)',
                                   'operator': rdflib.OWL.intersectionOf,
                                   'operands': (rdflib.URIRef('http://emmo.'
                                                              'info/emmo'
                                                              '/middle/math'
                                                              '#EMMO_54ee6b5e_'
                                                              '5261_44a8_86eb_'
                                                              '5717e7fdb9d0'),
                                                rdflib.URIRef('http://emmo.'
                                                              'info/emmo'
                                                              '/middle'
                                                              '/perceptual'
                                                              '#EMMO_a1083d0a_'
                                                              'c1fb_471f_8e20_'
                                                              'a98f881ad527')),
                                   }]

        # Example 2:
        #   (reductionistic.State OPERATOR.OR reductionistic.Existent)
        self.composition_data += [{'string': '(reductionistic.State '
                                             'OPERATOR.OR '
                                             'reductionistic.Existent)',
                                   'operator': rdflib.OWL.unionOf,
                                   'operands': (rdflib.URIRef('http://emmo'
                                                              '.info/emmo'
                                                              '/middle'
                                                              '/reductionistic'
                                                              '#EMMO_36c79456_'
                                                              'e29c_400d_8bd3_'
                                                              '0eedddb82652'),
                                                rdflib.URIRef('http://emmo'
                                                              '.info/emmo'
                                                              '/middle'
                                                              '/reductionistic'
                                                              '#EMMO_52211e5e_'
                                                              'd767_4812_845e_'
                                                              'eb6b402c476a')),
                                   }]

        # Example 3:
        #   (OPERATOR.NOT physicalistic.Matter)
        self.composition_data += [{'string': '(OPERATOR.NOT '
                                             'physicalistic.Matter)',
                                   'operator': rdflib.OWL.complementOf,
                                   'operands': (rdflib.URIRef('http://emmo'
                                                              '.info/emmo/'
                                                              'middle/'
                                                              'physicalistic'
                                                              '#EMMO_5b2222df_'
                                                              '4da6_442f_8244_'
                                                              '96e9e45887d1'),
                                                ),
                                   }]

        self.compositions = [self.build_composition(data)
                             for data in self.composition_data]

    @staticmethod
    def build_composition(data):
        """Returns a Composition object from a dictionary.

        Args:
            data (dict): The source dictionary. It is expected to have
            the following structure.
                {'string' (str): The string representation of the composition,
                 'operator' (rdflib.URIRef): Intersection, union or complement
                                             operations from the OWL ontology,
                 'operands' (list[rdflib.URIRef]): Classes on which the
                                                     composition acts,
                }
        """
        namespace_registry = math._namespace_registry
        graph = namespace_registry._graph

        # Create collection of operands if there is more than one.
        if len(data['operands']) > 1:
            collection = rdflib.collection.Collection(graph, rdflib.BNode())
            for operand in data['operands']:
                collection.append(operand)
            target = collection.uri
        elif len(data['operands']) == 1 \
                and data['operator'] == rdflib.OWL.complementOf:
            target = data['operands'][0]
        else:
            raise Exception(f'Illegal combination of operator '
                            f'{data["operator"]} and '
                            f'operands {data["operands"]}.')

        # Add collection of operands to the graph and create the composition.
        bnode = rdflib.BNode()
        graph.add((bnode, rdflib.RDF.type, rdflib.OWL.Class))
        graph.add((bnode, data['operator'], target))

        composition = Composition(bnode, namespace_registry)
        return composition

    def test___str__(self):
        """Tests the string representation of the composition.

        Also tests _compute_target, _check_quantifier and _add_operand
        implicitly.
        """
        for data, composition in zip(self.composition_data, self.compositions):
            self.assertEqual(data['string'], composition.__str__(),
                             f'The string representation of the composition'
                             f' does not match the expected one: '
                             f'{data["string"]}.')

    def test_operator(self):
        """Tests the operator method.

        Also tests _compute_target, _check_quantifier and _add_operand
        implicitly.
        """
        for data, composition in zip(self.composition_data, self.compositions):
            operator = predicate_to_operator[data['operator']]
            self.assertIs(operator, composition.operator)

    def test_operands(self):
        """Tests the operands method.

        Also tests _compute_target, _check_quantifier and _add_operand
        implicitly.
        """
        for data, composition in zip(self.composition_data, self.compositions):
            operand_identifiers = tuple(get_identifier(operand)
                                        for operand in composition.operands)
            self.assertEqual(data['operands'], operand_identifiers)


def get_identifier(operand):
    """Given an operand, compute its identifier (IRI or blank node).

    If the operand is already referenced by an identifier, no changes are
    performed on the input.
    """
    if isinstance(operand, rdflib.term.Identifier) \
            or isinstance(operand, rdflib.BNode):
        operand_identifier = operand
    elif isinstance(operand, OntologyEntity):
        operand_identifier = operand.iri
    elif isinstance(operand.target, Composition):
        operand_identifier = operand._bnode
    elif isinstance(operand.target, Restriction):
        operand_identifier = operand._bnode
    else:
        raise Exception(f"Unit test is incomplete, operands of type "
                        f"{type(operand)} are not considered.")
    return operand_identifier


if __name__ == "__main__":
    unittest.main()
