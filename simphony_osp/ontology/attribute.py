"""An attribute defined in the ontology."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterable, Iterator, Optional

from rdflib import OWL, RDF, RDFS, Literal, URIRef
from rdflib.term import Identifier

from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.utils.datatypes import UID, Triple, rdf_to_python

if TYPE_CHECKING:
    from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)


class OntologyAttribute(OntologyEntity):
    """An attribute defined in the ontology."""

    rdf_type = OWL.DatatypeProperty
    rdf_identifier = Identifier

    # Public API
    # ↓ ------ ↓

    @property
    def datatype(self) -> Optional[URIRef]:
        """Get the data type of the attribute.

        Returns:
            IRI of the datatype.

        Raises:
            NotImplementedError: More than one data type associated with the
                attribute.
        """
        data_types = (
            o
            for superclass in self.superclasses
            for o in self.session.graph.objects(superclass.iri, RDFS.range)
        )
        result = next(data_types, None)
        if next(data_types, None) is not None:
            raise NotImplementedError(
                f"More than one datatype associated to {self}: {data_types}."
            )
        return result

    # ↑ ------ ↑
    # Public API

    def __init__(
        self,
        uid: UID,
        session: Optional[Session] = None,
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

    def convert_to_datatype(self, value: Any) -> Any:
        """Convert the given value to a Python object.

        The class of the Python object depends on the data type of the
        attribute.

        Args:
            value: The value to convert.

        Returns:
            The converted value.
        """
        python_object = rdf_to_python(value, self.datatype)
        if isinstance(python_object, Literal):
            raise TypeError(
                f"Type '{type(value)}' of object {value} cannot be set as "
                f"attribute value, as it is either incompatible with the "
                f"OWL standard or not yet supported by SimPhoNy."
            )
        return python_object

    def _get_direct_superclasses(self) -> Iterator[OntologyAttribute]:
        """Get all the direct superclasses of this attribute.

        Returns:
            The direct superattributes.
        """
        for o in self.session.graph.objects(self.iri, RDFS.subPropertyOf):
            try:
                yield self.session.from_identifier_typed(
                    o, typing=OntologyAttribute
                )
            except TypeError:
                pass
        # The try-catch block makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.

    def _get_direct_subclasses(self) -> Iterator[OntologyAttribute]:
        """Get all the direct subclasses of this attribute.

        Returns:
            The direct subattributes.
        """
        for o in self.session.graph.subjects(RDFS.subPropertyOf, self.iri):
            try:
                yield self.session.from_identifier_typed(
                    o, typing=OntologyAttribute
                )
            except TypeError:
                pass
        # The try-catch makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.

    def _get_superclasses(self) -> Iterator[OntologyAttribute]:
        """Get all the superclasses of this attribute.

        Yields:
            The super-attributes.
        """
        yield self

        def closure(node, graph):
            yield from graph.objects(node, RDFS.subPropertyOf)

        for x in self.session.graph.transitiveClosure(
            closure, self.identifier
        ):
            try:
                yield self.session.from_identifier_typed(
                    x, typing=OntologyAttribute
                )
            except TypeError:
                pass
        # The filter makes sure that `OntologyAnnotation` and
        #  `OntologyRelationship` objects are not superclasses, as
        #  `RDFS.subPropertyOf` is used to establish class hierarchies of
        #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
        #  owl:AnnotationProperty.

        yield self.session.from_identifier(OWL.topDataProperty)

    def _get_subclasses(self) -> Iterator[OntologyAttribute]:
        """Get all the subclasses of this attribute.

        Yields:
            The sub-attributes.
        """
        yield self

        if self.identifier == OWL.topDataProperty:
            yield from (
                self.session.from_identifier_typed(s, typing=OntologyAttribute)
                for s in self.session.graph.subjects(
                    RDF.type, OWL.DatatypeProperty
                )
            )
        else:

            def closure(node, graph):
                yield from graph.subjects(RDFS.subPropertyOf, node)

            for x in self.session.graph.transitiveClosure(
                closure, self.identifier
            ):
                try:
                    yield self.session.from_identifier_typed(
                        x, typing=OntologyAttribute
                    )
                except TypeError:
                    pass
            # The filter makes sure that `OntologyAnnotation` and
            #  `OntologyRelationship` objects are not superclasses, as
            #  `RDFS.subPropertyOf` is used to establish class hierarchies of
            #  rdf:Property, owl:DatatypeProperty, owl:ObjectProperty and
            #  owl:AnnotationProperty.
