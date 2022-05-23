"""Special kind of ontology individual designed to organize entities."""

import logging
from typing import Iterable, Mapping, Optional

from simphony_osp.namespaces import simphony
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.session.session import Session
from simphony_osp.utils import simphony_namespace
from simphony_osp.utils.datatypes import UID, AttributeValue, Triple

logger = logging.getLogger(__name__)

buf_size = 1024


class File(OntologyIndividual):
    """Ontology individual representing a file."""

    rdf_type = simphony_namespace.File

    def __init__(
        self,
        uid: Optional[UID] = None,
        session: Optional[Session] = None,
        triples: Optional[Iterable[Triple]] = None,
        attributes: Optional[
            Mapping[OntologyAttribute, Iterable[AttributeValue]]
        ] = None,
        merge: bool = False,
    ) -> None:
        """Initialize the file."""
        super().__init__(
            uid=uid,
            session=session,
            triples=triples,
            class_=simphony.File,
            attributes=attributes,
            merge=merge,
        )
        logger.debug("Instantiated file %s" % self)

    def upload(self, path: str) -> None:
        """Upload a file.

        Queues a file to be uploaded to the server. When a commit is
        performed, the data is sent.
        """
        if hasattr(self.session.driver, "queue"):
            file = open(path, "rb")
            self.session.driver.queue(self.identifier, file)

    def download(self, path: str) -> None:
        """Download the file."""
        if hasattr(self.session.driver, "interface") and hasattr(
            self.session.driver.interface, "load"
        ):
            with self.session.driver.interface.load(self.identifier) as file:
                with open(path, "wb") as new_file:
                    data = True
                    while data:
                        data = file.read(buf_size)
                        new_file.write(data)
