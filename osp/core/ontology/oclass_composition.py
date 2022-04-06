"""This files defines composition of classes."""

import logging
from enum import Enum

from rdflib import OWL, RDF, BNode

logger = logging.getLogger(__name__)


class OPERATOR(Enum):
    """Operators to connect different classes."""

    AND = 1  # owl:intersectionOf
    OR = 2  # owl:unionOf
    NOT = 3  # owl:complementOf


class Composition:
    """Combine multiple classes using logical formulae."""

    def __init__(self, bnode, namespace_registry):
        """Initialize the class composition."""
        self._bnode = bnode
        self._graph = namespace_registry._graph
        self._namespace_registry = namespace_registry
        self._cached_operator = None
        self._cached_operands = None

    def __str__(self):
        """Transform to a Protege like string."""
        s = f" {self.operator} ".join(map(str, self.operands))
        if self.operator == OPERATOR.NOT:
            s = f"{self.operator} {s}"
        return f"({s})"

    @property
    def operator(self):
        """The operator that connects the different classes in the formula.

        Returns:
            OPERATOR: The operator Enum.
        """
        if self._cached_operator is None:
            self._compute()
        return self._cached_operator

    @property
    def operands(self):
        """The individual classes the formula is composed of.

        Returns:
            Union[OntologyClass, Composition, Restriction]: The operands.
        """
        if self._cached_operands is None:
            self._compute()
        return self._cached_operands

    def _compute(self):
        """Look up operator and operands in the graph."""
        for rdflib_predicate, operator in [
            (OWL.unionOf, OPERATOR.OR),
            (OWL.intersectionOf, OPERATOR.AND),
            (OWL.complementOf, OPERATOR.NOT),
        ]:
            if self._check_operator(rdflib_predicate, operator):
                return True

    def _check_operator(self, rdflib_predicate, operator):
        """Check if given operator is used and what the operands are."""
        self._cached_operands = list()
        o = self._graph.value(self._bnode, rdflib_predicate)
        if operator == OPERATOR.NOT:
            self._add_operand(operator, o)
            return True
        x = self._graph.value(o, RDF.first)
        while x:
            self._add_operand(operator, x)
            o = self._graph.value(o, RDF.rest)
            x = self._graph.value(o, RDF.first)
        return self._cached_operator is not None

    def _add_operand(self, operator, x):
        """Add a single operand to the list."""
        self._cached_operator = operator
        try:
            self._cached_operands.append(
                self._namespace_registry.from_bnode(x)
                if isinstance(x, BNode)
                else self._namespace_registry.from_iri(x)
            )
        except KeyError:
            pass


def get_composition(bnode, namespace_registry):
    """Return the restriction object represented by given bnode (or None)."""
    c = Composition(bnode, namespace_registry)
    if c.operands and c.operator:
        return c
