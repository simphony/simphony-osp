"""Special kind of ontology individual designed to organize entities."""

import logging
import os
import os.path
import shutil
import tempfile
from typing import Dict, Iterable, Optional

from rdflib import Literal

from simphony_osp.core.namespaces import cuba
from simphony_osp.core.ontology.attribute import OntologyAttribute
from simphony_osp.core.ontology.individual import OntologyIndividual
from simphony_osp.core.session import Session
from simphony_osp.core.utils.cuba_namespace import cuba_namespace
from simphony_osp.core.utils.datatypes import UID, AttributeValue, Triple


logger = logging.getLogger(__name__)


class File(OntologyIndividual):
    """Ontology individual representing a file."""

    rdf_type = cuba_namespace.File

    def __init__(self,
                 uid: Optional[UID] = None,
                 session: Optional[Session] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 attributes: Optional[
                     Dict[OntologyAttribute,
                          Iterable[AttributeValue]]] = None,
                 merge: bool = False,
                 ) -> None:
        """Initialize the file."""
        super().__init__(uid=uid,
                         session=session,
                         triples=triples,
                         class_=cuba.File,
                         attributes=attributes,
                         merge=merge,
                         )
        logger.debug("Instantiated file %s" % self)

    def upload(self) -> None:
        """Upload the file immediately.

        When a commit is performed, this file will already be on the server
        and thus be ignored.
        """
        if hasattr(self.session.graph.store, 'upload') \
                and self[cuba.path].any() is not None:
            self.session.graph.store.upload(
                {self.identifier: Literal(self[cuba.path].any())}
            )

    def download(self,
                 path: Optional[str] = None) -> None:
        """Download the file."""
        path = path or self[cuba.path].any()
        if hasattr(self.session.graph.store, 'download'):
            with tempfile.TemporaryDirectory() as temp_dir:
                self.session.graph.store.download(
                    self.identifier,
                    path=temp_dir
                )
                file = os.listdir(temp_dir)[0]
                shutil.move(os.path.join(temp_dir, file), path)
        elif path != self[cuba.path] and os.path.exists(self[cuba.path]):
            shutil.copy(self[cuba.path], path)
        else:
            raise FileNotFoundError(f"File {self[cuba.path]} not found.")

    def delete(self):
        """Delete the file from both the local and remote sides."""
        try:
            os.remove(self[cuba.path])
        except FileNotFoundError:
            pass
        self[cuba.path] = None
