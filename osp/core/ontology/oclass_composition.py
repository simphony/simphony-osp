"""This files defines composition of classes."""

import logging
from enum import Enum
from rdflib import OWL, BNode, RDF

logger = logging.getLogger(__name__)


class OPERATOR(Enum):
    """The operator of the composition."""
    AND = 1  # intersectionOf
    OR = 2  # unionOf
    NOT = 3  # complementOf


class Composition():
    """A class expression that is composed of several class expression."""

    def __init__(self, bnode, namespace_registry):
        """Initialize the class composition."""
        self._bnode = bnode
        self._graph = namespace_registry._graph
        self._namespace_registry = namespace_registry
        self._cached_operator = None
        self._cached_operands = None

    def __str__(self):
        """Transform it to a Protege like string."""
        s = f" {self.operator} ".join(map(str, self.operands))
        if self.operator == OPERATOR.NOT:
            s = f"{self.operator} {s}"
        return f"({s})"

    @property
    def operator(self):
        """The operator that connects the individual classes."""
        if self._cached_operator is None:
            self._compute()
        return self._cached_operator

    @property
    def operands(self):
        """The individual classes that are composed."""
        if self._cached_operands is None:
            self._compute()
        return self._cached_operands

    def _compute(self):
        """Query the graph to get operator and operands."""
        for rdflib_predicate, operator in [
            (OWL.unionOf, OPERATOR.OR),
            (OWL.intersectionOf, OPERATOR.AND),
            (OWL.complementOf, OPERATOR.NOT)
        ]:
            if self._check_operator(rdflib_predicate, operator):
                return True

    def _check_operator(self, rdflib_predicate, operator):
        """Check if given operator is used in the composition."""
        self._cached_operands = list()
        o = self._graph.value(self._bnode, rdflib_predicate)
        if operator == OPERATOR.NOT:
            self.add_operand(operator, o)
        x = self._graph.value(o, RDF.first)
        while x:
            self.add_operand(operator, x)
            o = self._graph.value(o, RDF.rest)
            x = self._graph.value(o, RDF.first)
        return self._cached_operator is not None

    def add_operand(self, operator, x):
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
