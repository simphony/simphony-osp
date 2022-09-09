"""This files defines composition of classes."""
from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union

from rdflib import OWL, RDF, BNode

from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.utils.datatypes import UID, Triple

if TYPE_CHECKING:
    from simphony_osp.ontology.oclass import OntologyClass
    from simphony_osp.ontology.restriction import Restriction
    from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)


class OPERATOR(Enum):
    """Operations applicable to class definitions."""

    AND = 1  # owl:intersectionOf
    OR = 2  # owl:unionOf
    NOT = 3  # owl:complementOf


class Composition(OntologyEntity):
    """Combinations of multiple classes using logical formulae."""

    rdf_type = OWL.Class
    rdf_identifier = BNode

    # Public API
    # ↓ ------ ↓

    @property
    def operator(self) -> OPERATOR:
        """The operator that connects the different classes in the formula.

        Returns:
            The operator Enum.
        """
        operator, _ = self._get_operator_and_operands()
        return operator

    @property
    def operands(
        self,
    ) -> Tuple[Union[OntologyClass, Composition, Restriction]]:
        """The individual classes the formula is composed of.

        Returns:
            The operands.
        """
        _, operands = self._get_operator_and_operands()
        return tuple(operands)

    # ↑ ------ ↑
    # Public API

    def __str__(self) -> str:
        """Transform to a Protege-like string."""
        s = f" {self.operator} ".join(map(str, self.operands))
        if self.operator == OPERATOR.NOT:
            s = f"{self.operator} {s}"
        return f"({s})"

    def __init__(
        self,
        uid: UID,
        session: Optional[Session] = None,
        triples: Optional[Iterable[Triple]] = None,
        merge: bool = False,
    ) -> None:
        """Initialize the class composition."""
        if not isinstance(uid.data, BNode):
            raise ValueError(
                f"Compositions are anonymous class descriptions, "
                f"and thus, they can only have blank nodes as "
                f"UIDs, not {type(uid.data)}."
            )
        super().__init__(uid, session, triples, merge=merge)

    def _get_operator_and_operands(
        self,
    ) -> Tuple[
        Optional[OPERATOR],
        List[Union[OntologyClass, Composition, Restriction]],
    ]:
        """Look up operator and operands in the graph."""
        for predicate, operator in [
            (OWL.unionOf, OPERATOR.OR),
            (OWL.intersectionOf, OPERATOR.AND),
            (OWL.complementOf, OPERATOR.NOT),
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

    def _get_operand(
        self, identifier
    ) -> Optional[Union[OntologyClass, Composition, Restriction]]:
        """Get an operand to the from an identifier."""
        try:
            operand = self.session.from_identifier(identifier)
            operand: Union[OntologyClass, Composition, Restriction]
            return operand
        except KeyError:
            pass

    def _get_direct_superclasses(self) -> Iterable[Composition]:
        """Compositions have no superclasses."""
        return iter(())

    def _get_direct_subclasses(self) -> Iterable[Composition]:
        """Compositions have no subclasses."""
        return iter(())

    def _get_superclasses(self) -> Iterable[Composition]:
        """Compositions have no superclasses."""
        return iter(())

    def _get_subclasses(self) -> Iterable[Composition]:
        """Compositions have no subclasses."""
        return iter(())
