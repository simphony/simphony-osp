"""This files defines composition of classes."""

import logging
from enum import Enum
from functools import lru_cache
from typing import Iterable, List, Optional, TYPE_CHECKING, Tuple, Union

from rdflib import OWL, BNode, RDF

from osp.core.ontology.datatypes import Triple, UID
from osp.core.ontology.entity import OntologyEntity

if TYPE_CHECKING:
    from osp.core.ontology.oclass import OntologyClass
    from osp.core.ontology.oclass_restriction import Restriction
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class OPERATOR(Enum):
    """Operators to connect different classes."""
    AND = 1  # owl:intersectionOf
    OR = 2  # owl:unionOf
    NOT = 3  # owl:complementOf


class Composition(OntologyEntity):
    """Combine multiple classes using logical formulae."""

    def __init__(self,
                 uid: UID,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None) -> None:
        """Initialize the class composition."""
        if not isinstance(uid.data, BNode):
            raise ValueError(f"Compositions are anonymous class descriptions, "
                             f"and thus, they can only have blank nodes as "
                             f"UIDs, not {type(uid.data)}.")
        super().__init__(uid, session, triples)

    def __str__(self) -> str:
        """Transform to a Protege-like string."""
        s = f" {self.operator} ".join(map(str, self.operands))
        if self.operator == OPERATOR.NOT:
            s = f"{self.operator} {s}"
        return f"({s})"

    @property
    def operator(self) -> OPERATOR:
        """The operator that connects the different classes in the formula.

        Returns:
            The operator Enum.
        """
        operator, _ = self._get_operator_and_operands
        return operator

    @property
    def operands(self) -> Tuple[Union['OntologyClass',
                                      'Composition',
                                      'Restriction']]:
        """The individual classes the formula is composed of.

        Returns:
            The operands.
        """
        _, operands = self._get_operator_and_operands
        return tuple(operands)

    @lru_cache(maxsize=None)
    def _get_operator_and_operands(self) -> \
            Tuple[Optional[OPERATOR],
                  List[Union['OntologyClass',
                             'Composition',
                             'Restriction']]]:
        """Look up operator and operands in the graph."""
        for predicate, operator in [
            (OWL.unionOf, OPERATOR.OR),
            (OWL.intersectionOf, OPERATOR.AND),
            (OWL.complementOf, OPERATOR.NOT)
        ]:
            operands = []
            o = self.session.graph.value(self.identifier, predicate)
            if operator == OPERATOR.NOT:
                operand = self._get_operand(o)
                operands += [operand] if operand is not None else []
                return operator, operands
            x = self.session.graph.value(o, RDF.first)
            while x:
                operand = self._get_operand(x)
                operands += [operand] if operand is not None else []
                o = self.session.graph.value(o, RDF.rest)
                x = self.session.graph.value(o, RDF.first)
            return operator, operands

    def _get_operand(self, identifier) -> Optional[Union['OntologyClass',
                                                         'Composition',
                                                         'Restriction']]:
        """Get an operand to the from an identifier."""
        try:
            return self.session.from_identifier(identifier)
        except KeyError:
            pass

    def _get_direct_superclasses(self) -> Iterable['OntologyEntity']:
        """Compositions have no superclasses."""
        return iter(())

    def _get_direct_subclasses(self) -> Iterable['OntologyEntity']:
        """Compositions have no subclasses."""
        return iter(())

    def _get_superclasses(self) -> Iterable['OntologyEntity']:
        """Compositions have no superclasses."""
        return iter(())

    def _get_subclasses(self) -> Iterable['OntologyEntity']:
        """Compositions have no subclasses."""
        return iter(())


def get_composition(identifier: BNode, session: 'Session'):
    """Return the restriction object represented by given BNode (or None)."""
    c = Composition(UID(identifier), session)
    if c.operands and c.operator:
        return c
