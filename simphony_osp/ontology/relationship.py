"""A relationship defined in the ontology."""

import logging
from typing import TYPE_CHECKING, Iterable, Iterator, Optional

from rdflib import OWL, RDFS
from rdflib.term import Identifier

from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.utils.datatypes import UID, Triple

if TYPE_CHECKING:
    from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)

# TODO characteristics


class OntologyRelationship(OntologyEntity):
    """A relationship defined in the ontology."""

    rdf_type = OWL.ObjectProperty
    rdf_identifier = Identifier

    def __init__(
        self,
        uid: UID,
        session: Optional["Session"] = None,
        triples: Optional[Iterable[Triple]] = None,
        merge: bool = False,
    ) -> None:
        """Initialize the ontology relationship.

        Args:
            uid: UID identifying the entity.
            session: Session where the entity is stored.
            triples: Construct the relationship with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
        """
        super().__init__(uid, session, triples, merge=merge)
        logger.debug("Create ontology relationship %s" % self)

    @property
    def inverse(self) -> Optional["OntologyRelationship"]:
        """Get the onverse relationship if it exists."""
        inverse = self.session.graph.objects(self.identifier, OWL.inverseOf)
        inverse = next(iter(inverse), None)
        inverse = (
            self.session.from_identifier(inverse)
            if inverse is not None
            else None
        )
        return inverse

    def _get_direct_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct superclasses of this relationship.

        Returns:
            The direct superrelationships.
        """
        return (
            self.session.from_identifier(o)
            for o in self.session.graph_and_overlay.objects(
                self.iri, RDFS.subPropertyOf
            )
        )

    def _get_direct_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct subclasses of this relationship.

        Returns:
            OntologyRelationship: The direct subrelationships
        """
        return (
            self.session.from_identifier(s)
            for s in self.session.graph_and_overlay.subjects(
                RDFS.subPropertyOf, self.iri
            )
        )

    def _get_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the superclasses of this relationship.

        Yields:
            The superrelationships.
        """
        yield self

        def closure(node, graph):
            for o in graph.objects(node, RDFS.subPropertyOf):
                yield o

        yield from (
            self.session.from_identifier(x)
            for x in self.session.graph_and_overlay.transitiveClosure(
                closure, self.identifier
            )
        )

        yield self.session.from_identifier(OWL.topObjectProperty)

    def _get_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the subclasses of this relationship.

        Yields:
            The subrelationships.
        """
        yield self

        def closure(node, graph):
            for s in graph.subjects(RDFS.subPropertyOf, node):
                yield s

        yield from (
            self.session.from_identifier(x)
            for x in self.session.graph_and_overlay.transitiveClosure(
                closure, self.identifier
            )
        )
