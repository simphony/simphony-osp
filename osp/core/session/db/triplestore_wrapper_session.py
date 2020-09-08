import uuid
import rdflib
from osp.core.utils import iri_from_uid, uid_from_iri
from osp.core.session.db.db_wrapper_session import DbWrapperSession
from abc import abstractmethod


class TripleStoreWrapperSession(DbWrapperSession):

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.

        for added in buffer.values():
            if added.uid == self.root:
                continue
            self._add(*added.get_triples())

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        # Perform the SQL-Statements to update the elements
        # in the buffers in the DB.
        for updated in buffer.values():
            if updated.uid == self.root:
                continue

            self._remove((updated.iri, None, None))
            self._add(*updated.get_triples())

    # OVERRIDE
    def _apply_deleted(self, root_obj, buffer):
        # Perform the SQL-Statements to delete the elements
        # in the buffers in the DB.
        for deleted in buffer.values():
            if deleted.uid == self.root:
                continue

            self._remove((deleted.iri, None, None))

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        for uid in uids:
            if uid == self.root:  # root not stored explicitly in database
                self._load_first_level()
                yield self._registry.get(uid)
                continue
            iri = iri_from_uid(uid)
            yield self._load_by_iri(iri)

    # OVERRIDE
    def _load_first_level(self):
        triple = (None, None, iri_from_uid(uuid.UUID(int=0)))
        uids = {
            uid_from_iri(s)
            for s, p, o in self._triples(triple)
        }
        list(self._load_from_backend(uids))

    # OVERRIDE
    def _load_by_oclass(self, oclass):
        uids = {
            uid_from_iri(s)
            for oc in oclass.subclasses
            for s, _, _ in self._triples((None, rdflib.RDF.type, oc.iri))
        }
        yield from self._load_from_backend(uids)

    @abstractmethod
    def _triples(self, pattern):
        """Get all triples that match the given pattern.

        Args:
            pattern (Tuple): A triple consisting of subject, predicate, object.
                Each can be None.
        """
        pass

    @abstractmethod
    def _add(self, *triples):
        """Add the triple to the database.

        Args:
            triples (Tuple): A tuple consisting of subject, predicate, object.
        """
        pass

    @abstractmethod
    def _remove(self, pattern):
        """Remove the triple from the database.

        Args:
            pattern (Tuple): A triple consisting of subject, predicate, object.
                Each can be None.
        """
        pass

    @abstractmethod
    def _load_by_iri(self, iri):
        """Load the CUDS object with the given IRI.

        Args:
            iri (Tuple): The IRI of the CUDS object to load.
        """
        pass
