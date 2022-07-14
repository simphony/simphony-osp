"""Special kind of ontology individual designed to organize entities."""
from __future__ import annotations

import logging
from typing import BinaryIO

from rdflib.term import URIRef

from simphony_osp.ontology.operations import Operations
from simphony_osp.utils.simphony_namespace import simphony_namespace

logger = logging.getLogger(__name__)

buf_size = 1024


class File(Operations):
    """Actions for ontology individuals representing a file."""

    iri: str = str(simphony_namespace.File)

    @property
    def _session(self):
        """Session of the ontology individual connected to the action."""
        return self._individual.session

    @property
    def _identifier(self) -> URIRef:
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

    def upload(self, path: str) -> None:
        """Upload a file.

        Queues a file to be uploaded to the server. When a commit is
        performed, the data is sent.
        """
        if self._session.driver is not None:
            file = open(path, "rb")
            self._session.driver.queue(self._identifier, file)
        else:
            logger.warning(
                "This session does not support saving new files. The "
                "contents of the file will NOT be saved."
            )

    def download(self, path: str) -> None:
        """Download the file."""
        if self._session.driver is not None:
            with self._session.driver.load(self._identifier) as file:
                with open(path, "wb") as new_file:
                    data = True
                    while data:
                        data = file.read(buf_size)
                        new_file.write(data)
        else:
            raise FileNotFoundError(
                "This session does not support file storage. Unable to "
                "retrieve the file contents."
            )

    @property
    def handle(self) -> BinaryIO:
        """Get a file handle to operate with."""
        if self._session.driver is not None:
            return self._session.driver.load(self._identifier)
        else:
            raise FileNotFoundError(
                "This session does not support file storage. Unable to "
                "retrieve the file contents."
            )

    def overwrite(self, contents: BinaryIO) -> None:
        """Overwrite the file contents with a byte stream."""
        if self._session.driver is not None:
            self._session.driver.queue(self._identifier, contents)
        else:
            logger.warning(
                "This session does not support saving new files. The "
                "contents of the file will NOT be saved."
            )
