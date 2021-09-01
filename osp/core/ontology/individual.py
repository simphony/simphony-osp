"""An ontology individual."""

import logging
from typing import Dict, Iterable, Optional, TYPE_CHECKING, Tuple, Union

from rdflib import OWL, RDF, RDFS, XSD, BNode, Graph, Literal, URIRef

from osp.core.ontology.datatypes import UID, RDFCompatibleType, Triple
from osp.core.ontology.entity import OntologyEntity

if TYPE_CHECKING:
    from osp.core.ontology.attribute import OntologyAttribute
    from osp.core.ontology.oclass import OntologyClass
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class OntologyIndividual(OntologyEntity):
    """An ontology individual."""

    def __init__(self,
                 uid: Optional[UID] = None,
                 session: Optional['Session'] = None,
                 class_: Optional['OntologyClass'] = None,
                 attributes: Optional[
                     Dict['OntologyAttribute',
                          Iterable[RDFCompatibleType]]] = None,
                 extra_triples:  Iterable[Triple] = tuple(),
                 ) -> None:
        """Initialize the ontology class.

        Args:
            uid: UID identifying the ontology individual.
            session: Session where the entity is stored.
        """
        if uid is None:
            uid = UID()
        elif not isinstance(uid, UID):
            raise Exception(f"Tried to initialize an ontology individual with "
                            f"uid {uid}, which is not a UID object.")

        self._ontology_classes = []

        # The ontology individual is initialized in a temporary session
        # where it is constructed.
        # TODO: Use the simplest possible session class.
        super().__init__(uid, Session())

        for k, v in attributes.items():
            for e in v:
                self.session.graph.add((
                    self.iri, k.iri, Literal(k.convert_to_datatype(e),
                                             datatype=k.datatype)
                ))

        if class_:
            self.session.graph.add((
                self.iri, RDF.type, class_.iri
            ))
            self._ontology_classes += [class_]
        extra_class = False
        for s, p, o in extra_triples:
            if s != self.identifier:
                raise ValueError("Trying to add extra triples to an ontology "
                                 "individual with a subject that does not "
                                 "match the individual's identifier.")
            elif p == RDF.type:
                extra_class = True
            self.session.graph.add((s, p, o))
            # TODO: grab extra class from tbox, add it to _ontology_classes.
        class_assigned = bool(class_) or extra_class
        if not class_assigned:
            raise TypeError(f"No ontology class associated with {self}! "
                            f"Did you install the required ontology?")

        # When the construction is complete, the session is switched.
        session.store(self)
        self._session = session
        logger.debug("Instantiated ontology individual %s" % self)

    @property
    def uid(self) -> UID:
        return super().uid

    @uid.setter
    def uid(self, value: UID) -> UID:
        raise NotImplementedError("Changing the unique identifier of an "
                                  "ontology individual is not yet supported.")
        # TODO: allow this, should be rather simple, just replace all
        #  occurrences of the IRI by the new one.

    @property
    def oclasses(self) -> Tuple['OntologyClass']:
        """Get the ontology classes of this ontology individual."""
        return tuple(self._ontology_classes)

    @property
    def oclass(self) -> Optional[OntologyClass]:
        """Get the type of the ontology individual."""
        oclasses = self.oclasses
        return oclasses[0] if oclasses else None

    def is_a(self, oclass: 'OntologyClass') -> bool:
        """Check if the ontology individual is an instance of the given oclass.

        Args:
            oclass: Check if the ontology individual is an instance of this
                oclass.

        Returns:
            bool: Whether the ontology individual is an instance of the given
                oclass.
        """
        return any(oc in oclass.subclasses for oc in self.oclasses)