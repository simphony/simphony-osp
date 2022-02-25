"""An attribute defined in the ontology."""

import logging
from typing import Any, Iterable, Iterator, Optional, TYPE_CHECKING

from rdflib import OWL, RDFS, URIRef
from rdflib.term import Identifier

from simphony_osp.core.ontology.entity import OntologyEntity
from simphony_osp.core.utils.datatypes import rdf_to_python, Triple, UID

if TYPE_CHECKING:
    from simphony_osp.core.session import Session

logger = logging.getLogger(__name__)


class OntologyAttribute(OntologyEntity):
    """An attribute defined in the ontology."""

    rdf_type = OWL.DatatypeProperty
    rdf_identifier = Identifier

    @property
    def datatype(self) -> Optional[URIRef]:
        """Get the data type of the attribute.

        Returns:
            IRI of the datatype.

        Raises:
            NotImplementedError: More than one data type associated with the
                attribute.
        """
        data_types = set(
            o for superclass in self.superclasses
            for o in self.session.graph.objects(
                superclass.iri, RDFS.range))
        result = set(data_types)
        if len(result) > 1:
            raise NotImplementedError(
                f"More than one datatype associated to {self}: {data_types}.")
        return result.pop() if len(result) > 0 else None

    def __init__(self,
                 uid: UID,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False,
                 ) -> None:
        """Initialize the ontology attribute.

        Args:
            uid: UID identifying the entity.
            session: Session where the entity is stored.
            triples: Construct the attribute with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
        """
        super().__init__(uid, session, triples, merge=merge)
        logger.debug("Instantiated ontology attribute %s." % self)

    def convert_to_datatype(self, value: Any) -> Any:
        """Convert the value to the Python datatype of the attribute.

        Args:
            value: The value to convert.

        Returns:
            The converted value.
        """
        return rdf_to_python(value, self.datatype)

    def _get_direct_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct superclasses of this attribute.

        Returns:
            The direct superattributes.
        """
        return filter(
            lambda x: isinstance(x, OntologyAttribute),
            (self.session.from_identifier(o)
             for o in self.session.graph.objects(self.iri,
                                                 RDFS.subPropertyOf))
        )
        # The filter makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.

    def _get_direct_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct subclasses of this attribute.

        Returns:
            The direct subattributes.
        """
        return filter(
            lambda x: isinstance(x, OntologyAttribute),
            (self.session.from_identifier(s)
             for s in self.session.graph.subjects(RDFS.subPropertyOf,
                                                  self.iri)),
        )
        # The filter makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.

    def _get_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the superclasses of this attribute.

        Yields:
            The superattributes.
        """
        yield self

        def closure(node, graph):
            for o in graph.objects(node, RDFS.subPropertyOf):
                yield o

        yield from filter(
            lambda x: isinstance(x, OntologyAttribute),
            (self.session.from_identifier(x)
             for x in self.session.graph.transitiveClosure(closure,
                                                           self.identifier))
        )
        # The filter makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.

        yield self.session.from_identifier(OWL.topDataProperty)

    def _get_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the subclasses of this attribute.

        Yields:
            The subattributes.
        """
        yield self

        def closure(node, graph):
            for s in graph.subjects(RDFS.subPropertyOf, node):
                yield s

        yield from filter(
            lambda x: isinstance(x, OntologyAttribute),
            (self.session.from_identifier(x)
             for x in self.session.graph.transitiveClosure(closure,
                                                           self.identifier)))
        # The filter makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.
