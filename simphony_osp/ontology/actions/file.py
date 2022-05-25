"""Special kind of ontology individual designed to organize entities."""

import logging
from typing import TYPE_CHECKING

from rdflib.term import URIRef

from simphony_osp.ontology.actions import Actions, action
from simphony_osp.utils import simphony_namespace

if TYPE_CHECKING:
    from simphony_osp.ontology.individual import OntologyIndividual

logger = logging.getLogger(__name__)

buf_size = 1024


class File(Actions):
    """Actions for ontology individuals representing a file."""

    iri: str = str(simphony_namespace.File)

    def __init__(self, individual: "OntologyIndividual"):
        """Initialize the collection of file actions."""
        self._individual: "OntologyIndividual" = individual

    @property
    def session(self):
        """Session of the ontology individual connected to the action."""
        return self._individual.session

    @property
    def identifier(self) -> URIRef:
        """Identifier of the ontology individual connected to the action.

        Only `URIRef` objects are allowed.
        """
        identifier = self._individual.identifier
        if not isinstance(identifier, URIRef):
            raise TypeError(
                f"Invalid identifier type "
                f"{type(identifier)} for file individual."
            )
        return identifier

    @action
    def upload(self, path: str) -> None:
        """Upload a file.

        Queues a file to be uploaded to the server. When a commit is
        performed, the data is sent.
        """
        if hasattr(self.session.driver, "queue"):
            file = open(path, "rb")
            self.session.driver.queue(self.identifier, file)

    @action
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
