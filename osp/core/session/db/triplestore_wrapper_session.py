import uuid
import rdflib
from osp.core.utils import create_from_triples
from osp.core.utils import iri_from_uid, uid_from_iri
from osp.core.session.db.db_wrapper_session import DbWrapperSession
from osp.core.namespaces import from_iri
from abc import abstractmethod


class TripleStoreWrapperSession(DbWrapperSession):

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.

        for added in buffer.values():
            if added.uid == self.root:
                continue
            triples = self._substitute_root_iri(added.get_triples())
            self._add(*triples)

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        # Perform the SQL-Statements to update the elements
        # in the buffers in the DB.
        for updated in buffer.values():
            if updated.uid == self.root:
                continue

            self._remove((updated.iri, None, None))
            triples = self._substitute_root_iri(updated.get_triples())
            self._add(*triples)

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
        triple = (None, None, iri_from_uid(self.root))
        triple = next(self._substitute_root_iri([triple]))
        uids = {
            uid_from_iri(s)
            for s, p, o in self._triples(triple)
        }
        uids = {x if x != uuid.UUID(int=0) else self. root for x in uids}
        list(self._load_from_backend(uids))

    # OVERRIDE
    def _load_by_oclass(self, oclass):
        uids = {
            uid_from_iri(s)
            for oc in oclass.subclasses
            for s, _, _ in self._triples((None, rdflib.RDF.type, oc.iri))
        }
        uids = {x if x != uuid.UUID(int=0) else self. root for x in uids}
        yield from self._load_from_backend(uids)

    def _substitute_root_iri(self, triples):
        from osp.core.utils import CUDS_IRI_PREFIX
        for triple in triples:
            yield tuple(iri_from_uid(uuid.UUID(int=0))
                        if x is not None and x.startswith(CUDS_IRI_PREFIX)
                        and uid_from_iri(x) == self.root else x
                        for x in triple)

    def _load_by_iri(self, iri):
        """Load the CUDS object wit the given IRI.

        Args:
            iri (rdflib.IRI): The IRI of the CUDS object to oad.

        Returns:
            Cuds - The CUDS object with the given IRI.
        """
        if iri == iri_from_uid(self.root):
            iri = iri_from_uid(uuid.UUID(int=0))
        _triples, type_triples_of_neighbors = self._load_triples_for_iri(iri)
        triples, neighbor_triples = [], []
        for s, p, o in _triples:
            if o == iri_from_uid(uuid.UUID(int=0)):
                triples.append((s, p, iri_from_uid(self.root)))
                neighbor_triples.append((iri_from_uid(self.root),
                                         from_iri(p).inverse.iri,
                                         s))
            else:
                triples.append((s,p, o))
        for s, p, o in type_triples_of_neighbors:
            if s == iri_from_uid(uuid.UUID(int=0)):
                neighbor_triples.append((iri_from_uid(self.root), p, o))
            else:
                neighbor_triples.append((s, p, o))

        return create_from_triples(
            triples=triples,
            neighbor_triples=neighbor_triples,
            session=self
        )


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
    def _load_triples_for_iri(self, iri):
        """Load the all triples for the CUDS object with the given IRI.

        Args:
            iri (Tuple): The IRI of the CUDS object to load the triples for.
        """
        pass
