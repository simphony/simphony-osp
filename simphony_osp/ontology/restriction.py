"""Restrictions on ontology classes."""
from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Iterable, Optional, Tuple, Union

from rdflib import OWL, BNode, URIRef
from rdflib.term import Identifier

from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.utils.datatypes import UID, Triple

if TYPE_CHECKING:
    from simphony_osp.ontology.oclass import OntologyClass
    from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)


class QUANTIFIER(Enum):
    """Quantifiers for restrictions."""

    SOME: int = 1
    ONLY: int = 2
    EXACTLY: int = 3
    MIN: int = 4
    MAX: int = 5
    VALUE: int = 6


class RTYPE(Enum):
    """Types of restrictions."""

    ATTRIBUTE_RESTRICTION = 1
    RELATIONSHIP_RESTRICTION = 2


class Restriction(OntologyEntity):
    """Restrictions on ontology classes."""

    rdf_type = OWL.Restriction
    rdf_identifier = BNode

    def __init__(
        self,
        uid: UID,
        session: Optional[Session] = None,
        triples: Optional[Iterable[Triple]] = None,
        merge: bool = False,
    ) -> None:
        """Initialize the restriction class.

        Args:
            uid: An UID whose data attribute is the blank node that represents
                the restriction.
            session: Session where the restriction is stored.
            triples: Construct the restriction with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
        """
        if not isinstance(uid.data, BNode):
            raise ValueError(
                f"Restrictions are anonymous class descriptions, "
                f"and thus, they can only have blank nodes as "
                f"UID, not {type(uid.data)}."
            )
        super().__init__(uid, session, triples, merge=merge)

    def __str__(self) -> str:
        """Transform to string."""
        return " ".join(
            map(str, (self._property, self.quantifier, self.target))
        )

    # Public API
    # ↓ ------ ↓

    @property
    def quantifier(self) -> QUANTIFIER:
        """Get the quantifier of the restriction.

        Returns:
            The quantifier of the restriction.
        """
        quantifier, _ = self._get_quantifier_and_target()
        return quantifier

    @property
    def target(self) -> Union[OntologyClass, URIRef]:
        """The target ontology class or datatype.

        Returns:
            The target class or datatype.
        """
        quantifier, target = self._get_quantifier_and_target()
        try:
            target = self.session.from_identifier(target)
        except KeyError:
            pass
        return target

    @property
    def relationship(self) -> OntologyRelationship:
        """The relationship that the RELATIONSHIP_RESTRICTION acts on.

        Raises:
            AttributeError: Called on an ATTRIBUTE_RESTRICTION.

        Returns:
            The relationship the restriction acts on.
        """
        if self.rtype == RTYPE.ATTRIBUTE_RESTRICTION:
            raise AttributeError
        return self._property

    @property
    def attribute(self) -> OntologyAttribute:
        """The attribute that the ATTRIBUTE_RESTRICTION acts on.

        Raises:
            AttributeError: Called on a RELATIONSHIP_RESTRICTION.

        Returns:
            The attribute.
        """
        if self.rtype == RTYPE.RELATIONSHIP_RESTRICTION:
            raise AttributeError
        return self._property

    @property
    def rtype(self) -> RTYPE:
        """Type of restriction.

        Whether the restriction acts on attributes or relationships.

        Returns:
            RTYPE: The type of restriction.
        """
        prop = self._property
        if isinstance(prop, OntologyRelationship):
            return RTYPE.RELATIONSHIP_RESTRICTION
        elif isinstance(prop, OntologyAttribute):
            return RTYPE.ATTRIBUTE_RESTRICTION
        else:
            raise RuntimeError(
                f"Invalid property {prop} for restriction. "
                f"{OntologyRelationship} or {OntologyAttribute}"
                f" were expected."
            )

    # ↑ ------ ↑
    # Public API

    def _get_quantifier_and_target(
        self,
    ) -> Tuple[Optional[QUANTIFIER], Optional[Identifier]]:
        """Get both the quantifier and the target of the restriction.

        Since the calculation of one involves the calculation of the other,
        this function returns both, and caches the result. Then,
        then each individual element can be queried through the properties
        `quantifier` and `target`.

        Returns:
            A tuple where the first element is a quantifier (if any) and
            the second element the identifier of the target (if any).
        """
        for predicate, quantifier in [
            (OWL.someValuesFrom, QUANTIFIER.SOME),
            (OWL.allValuesFrom, QUANTIFIER.ONLY),
            (OWL.cardinality, QUANTIFIER.EXACTLY),
            (OWL.qualifiedCardinality, QUANTIFIER.EXACTLY),
            (OWL.minCardinality, QUANTIFIER.MIN),
            (OWL.minQualifiedCardinality, QUANTIFIER.MIN),
            (OWL.maxCardinality, QUANTIFIER.MAX),
            (OWL.maxQualifiedCardinality, QUANTIFIER.MAX),
            (OWL.hasValue, QUANTIFIER.VALUE),
        ]:
            x = self.session.graph.value(self.identifier, predicate)
            if x:
                return quantifier, x
        else:
            return None, None

    @property
    def _property(self) -> Union[OntologyRelationship, OntologyAttribute]:
        """The relationship or attribute the restriction acts on.

        Returns:
            Union[OntologyRelationship, OntologyAttribute]:
                object of owl:onProperty predicate.
        """
        prop = self.session.graph.value(self.identifier, OWL.onProperty)
        if prop and not isinstance(prop, BNode):
            # TODO: handle inverse properties defined as blank nodes.
            return self.session.from_identifier(prop)
        else:
            raise RuntimeError(
                f"Property {prop} is not within any installed " f"ontology."
            )

    def _get_direct_superclasses(self) -> Iterable[OntologyEntity]:
        """Restrictions have no superclasses."""
        return iter(())

    def _get_direct_subclasses(self) -> Iterable[OntologyEntity]:
        """Restrictions have no subclasses."""
        return iter(())

    def _get_superclasses(self) -> Iterable[OntologyEntity]:
        """Restrictions have no superclasses."""
        return iter(())

    def _get_subclasses(self) -> Iterable[OntologyEntity]:
        """Restrictions have no subclasses."""
        return iter(())
