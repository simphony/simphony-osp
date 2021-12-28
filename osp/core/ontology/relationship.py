"""A relationship defined in the ontology."""

import logging
from typing import Iterable, Iterator, Optional, TYPE_CHECKING

from rdflib import OWL, RDFS
from rdflib.term import Identifier

from osp.core.ontology.entity import OntologyEntity
from osp.core.utils.datatypes import Triple, UID

if TYPE_CHECKING:
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)

# TODO characteristics


class OntologyRelationship(OntologyEntity):
    """A relationship defined in the ontology."""

    rdf_type = OWL.ObjectProperty
    rdf_identifier = Identifier

    def __init__(self,
                 uid: UID,
                 session: Optional['Session'] = None,
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

    def _get_direct_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct superclasses of this relationship.

        Returns:
            The direct superrelationships.
        """
        return (self.session.from_identifier(o) for o in
                self.session.ontology_graph.objects(
                    self.iri, RDFS.subPropertyOf))

    def _get_direct_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct subclasses of this relationship.

        Returns:
            OntologyRelationship: The direct subrelationships
        """
        return (self.session.from_identifier(s) for s in
                self.session.ontology_graphgraph.subjects(
                    RDFS.subPropertyOf, self.iri))

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
            for x in self.session.ontology_graph.transitiveClosure(
                closure, self.identifier))

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
            for x in self.session.ontology_graph.transitiveClosure(
                closure, self.identifier))
