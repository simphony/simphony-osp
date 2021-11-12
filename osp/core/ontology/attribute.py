"""An attribute defined in the ontology."""

import logging
from typing import Any, Iterable, Iterator, Optional, TYPE_CHECKING

from rdflib import RDFS, XSD, Literal, URIRef

from osp.core.ontology.datatypes import RDF_TO_PYTHON, Triple, UID
from osp.core.ontology.entity import OntologyEntity

if TYPE_CHECKING:
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class OntologyAttribute(OntologyEntity):
    """An attribute defined in the ontology."""

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
        # TODO: Very similar to
        #  `osp.core.session.interfaces.sql_wrapper_session.SqlWrapperSession
        #  ._convert_to_datatype`. Unify somehow.
        if isinstance(value, Literal):
            result = Literal(value.toPython(), datatype=self.datatype,
                             lang=value.language).toPython()
            if isinstance(result, Literal):
                result = RDF_TO_PYTHON[self.datatype or XSD.string](
                    value.value)
        else:
            result = RDF_TO_PYTHON[self.datatype or XSD.string](value)
        return result

    def _get_direct_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct superclasses of this attribute.

        Returns:
            The direct superattributes.
        """
        return (self.session.from_identifier(o) for o in
                self.session.graph.objects(self.iri, RDFS.subPropertyOf))

    def _get_direct_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct subclasses of this attribute.

        Returns:
            The direct subattributes.
        """
        return (self.session.from_identifier(s) for s in
                self.session.graph.subjects(RDFS.subPropertyOf, self.iri))

    def _get_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the superclasses of this attribute.

        Yields:
            The superattributes.
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
        """Get all the subclasses of this attribute.

        Yields:
            The subattributes.
        """
        yield self

        def closure(node, graph):
            for s in graph.subjects(RDFS.subPropertyOf, node):
                yield s

        yield from (
            self.session.from_identifier(x)
            for x in self.session.graph.transitiveClosure(closure,
                                                          self.identifier))
