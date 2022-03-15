"""A session connecting to a backend which stores the CUDS in triples."""

from abc import abstractmethod

from rdflib import RDF, URIRef

from osp.core.ontology.datatypes import UID
from osp.core.session.db.db_wrapper_session import DbWrapperSession
from osp.core.session.sparql_backend import SPARQLBackend
from osp.core.utils.wrapper_development import create_from_triples


class TripleStoreWrapperSession(DbWrapperSession, SPARQLBackend):
    """A session connecting to a backend which stores the CUDS in triples."""

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.
        triples = (triple for added in buffer.values() for triple
                   in self._substitute_root_iri(added.get_triples()))
        self._add(*triples)

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        # Perform the SQL-Statements to update the elements
        # in the buffers in the DB.
        # TODO: maybe _remove should accept multiple patterns at once,
        #  as _add does. Changing this should only break the AllegroGraph
        #  wrapper.
        for updated in buffer.values():
            pattern = (updated.iri, None, None)
            self._remove(next(self._substitute_root_iri([pattern])))
        triples_add = (triple for updated in buffer.values()
                       for triple in
                       self._substitute_root_iri(updated.get_triples()))
        self._add(*triples_add)

    # OVERRIDE
    def _apply_deleted(self, root_obj, buffer):
        # Perform the SQL-Statements to delete the elements
        # in the buffers in the DB.
        # TODO: maybe _remove should accept multiple patterns at once,
        #  as _add does. Changing this should only break the AllegroGraph
        #  wrapper.
        for deleted in buffer.values():
            pattern = (deleted.iri, None, None)
            self._remove(next(self._substitute_root_iri([pattern])))

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        for uid in uids:
            iri = uid.to_iri()
            yield self._load_by_iri(iri)

    # OVERRIDE
    def _load_first_level(self):
        triple = (self.root.to_iri(), None, None)
        triple = next(self._substitute_root_iri([triple]))
        iris = {
            o for s, p, o in self._triples(triple)
            if isinstance(o, URIRef)
            and self._is_cuds_iri_ontology(o)
            and UID(o) != UID(0)
        }
        iris.add(self.root.to_iri())
        for iri in iris:
            self._load_by_iri(iri)

    # OVERRIDE
    def _load_by_oclass(self, oclass):
        uids = {
            UID(s)
            for s, _, _ in self._triples((None, RDF.type, oclass.iri))
        }
        uids = {x if x != UID(0) else self. root for x in uids}
        yield from self._load_from_backend(uids)

    def _substitute_root_iri(self, triples):
        from osp.core.utils.general import CUDS_IRI_PREFIX
        for triple in triples:
            yield tuple(UID(0).to_iri()
                        if x is not None and x.startswith(CUDS_IRI_PREFIX)
                        and UID(x) == self.root else x
                        for x in triple)

    def _substitute_zero_iri(self, triples):
        from osp.core.utils.general import CUDS_IRI_PREFIX
        for triple in triples:
            yield tuple(self.root.to_iri()
                        if x is not None and x.startswith(CUDS_IRI_PREFIX)
                        and UID(x) == UID(0) else x
                        for x in triple)

    def _load_by_iri(self, iri):
        """Load the CUDS object wit the given IRI.

        Args:
            iri (IRI): The IRI of the CUDS object to oad.

        Returns:
            Cuds - The CUDS object with the given IRI.
        """
        if iri == self.root.to_iri():
            iri = UID(0).to_iri()
        triples, neighbor_triples = self._load_triples_for_iri(iri)

        triples = self._substitute_zero_iri(triples)
        neighbor_triples = self._substitute_zero_iri(neighbor_triples)

        return create_from_triples(
            triples=triples,
            neighbor_triples=neighbor_triples,
            session=self,
            fix_neighbors=False
        )

    @abstractmethod
    def _triples(self, pattern):
        """Get all triples that match the given pattern.

        Args:
            pattern (Tuple): A triple consisting of subject, predicate, object.
                Each can be None.
        """

    @abstractmethod
    def _add(self, *triples):
        """Add the triple to the database.

        Args:
            triples (Tuple): A tuple consisting of subject, predicate, object.
        """

    @abstractmethod
    def _remove(self, pattern):
        """Remove all triple that match the given rdflib Pattern.

        A pattern is a 3-tuple of rdflib terms(URIRef and Literal),
        but unlike triples it can have placeholders(None values).
        These None values will be replaced by matching the patterns with
        the triples stored in the graph.

        Args:
            pattern (Tuple): A triple consisting of subject, predicate, object.
                Each can be None.
        """

    def _load_triples_for_iri(self, iri):
        """Load the all triples for the CUDS object with the given IRI.

        Args:
            iri (Tuple): The IRI of the CUDS object to load the triples for.
        """
        triples = set(self._triples((iri, None, None)))
        type_triples_of_neighbors = set()
        for s, p, o in triples:
            if isinstance(o, URIRef):
                type_triples_of_neighbors |= set(
                    self._triples((o, RDF.type, None))
                )
        return triples, type_triples_of_neighbors
