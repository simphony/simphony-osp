"""An annotation property defined in the ontology."""

import logging
from typing import Iterable, Iterator, TYPE_CHECKING, Optional

from rdflib import RDF, RDFS, OWL
from rdflib.term import Identifier

from osp.core.utils.datatypes import Triple, UID
from osp.core.ontology.entity import OntologyEntity

if TYPE_CHECKING:
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class OntologyAnnotation(OntologyEntity):
    """An annotation property defined in the ontology."""

    rdf_type = {OWL.AnnotationProperty, RDF.Property}
    rdf_identifier = Identifier

    def __init__(self,
                 uid: UID,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False,
                 ) -> None:
        """Initialize the ontology annotation.

        Args:
            uid: UID identifying the entity.
            session: Session where the entity is stored.
            triples: Construct the annotation with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
        """
        super().__init__(uid, session, triples, merge=merge)
        logger.debug("Create ontology annotation property %s" % self)

    def _get_direct_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct superclasses of this annotation.

        Returns:
            The direct superannotations.
        """
        return (self.session.from_identifier(o) for o in
                self.session.graph.objects(self.iri, RDFS.subPropertyOf))

    def _get_direct_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct subclasses of this annotation.

        Returns:
            OntologyRelationship: The direct subannotations
        """
        return (self.session.from_identifier(s) for s in
                self.session.graph.subjects(RDFS.subPropertyOf, self.iri))

    def _get_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the superclasses of this annotation.

        Yields:
            The superannotations.
        """
        yield self

        def closure(node, graph):
            for o in graph.objects(node, RDFS.subPropertyOf):
                yield o

        yield from (
            self.session.from_identifier(x)
            for x in self.session.graph.transitiveClosure(closure,
                                                          self.identifier))

    def _get_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the subclasses of this annotation.

        Yields:
            The subannotations.
        """
        yield self

        def closure(node, graph):
            for s in graph.subjects(RDFS.subPropertyOf, node):
                yield s

        yield from (
            self.session.from_identifier(x)
            for x in self.session.graph.transitiveClosure(closure,
                                                          self.identifier))
