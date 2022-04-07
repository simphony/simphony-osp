"""A session connecting to a backend which stores the CUDS in triples."""

from abc import abstractmethod
from uuid import UUID

from rdflib import RDF, URIRef

from osp.core.session.db.db_wrapper_session import DbWrapperSession
from osp.core.session.sparql_backend import SPARQLBackend
from osp.core.utils.general import CUDS_IRI_PREFIX, iri_from_uid, uid_from_iri
from osp.core.utils.wrapper_development import create_from_triples


class TripleStoreWrapperSession(DbWrapperSession, SPARQLBackend):
    """A session connecting to a backend which stores the CUDS in triples."""

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.
        triples = (
            triple
            for added in buffer.values()
            for triple in self._substitute_root_iri(added.get_triples())
        )
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
        triples_add = (
            triple
            for updated in buffer.values()
            for triple in self._substitute_root_iri(updated.get_triples())
        )
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
        yield from self._load_by_iri(*(iri_from_uid(uid) for uid in uids))

    # OVERRIDE
    def _load_first_level(self):
        root_iri = iri_from_uid(self.root)
        zero_iri = iri_from_uid(UUID(int=0))
        triple = (root_iri, None, None)
        triple = next(self._substitute_root_iri([triple]))
        iris = {
            o
            for s, p, o in self._triples(triple)
            if isinstance(o, URIRef)
            and self._is_cuds_iri_ontology(o)
            and o != zero_iri
        }
        iris |= {root_iri}
        for _ in self._load_by_iri(*iris):
            pass  # Just exhaust the iterator so that CUDS are actually loaded.

    # OVERRIDE
    def _load_by_oclass(self, oclass):
        uids = {
            uid_from_iri(s)
            for s, _, _ in self._triples((None, RDF.type, oclass.iri))
        }
        uids = {x if x != UUID(int=0) else self.root for x in uids}
        yield from self._load_from_backend(uids)

    def _substitute_root_iri(self, triples):
        for triple in triples:
            yield tuple(
                iri_from_uid(UUID(int=0))
                if x is not None
                and x.startswith(CUDS_IRI_PREFIX)
                and uid_from_iri(x) == self.root
                else x
                for x in triple
            )

    def _substitute_zero_iri(self, triples):
        for triple in triples:
            yield tuple(
                iri_from_uid(self.root)
                if x is not None
                and x.startswith(CUDS_IRI_PREFIX)
                and uid_from_iri(x) == UUID(int=0)
                else x
                for x in triple
            )

    def _load_by_iri(self, *iris: URIRef):
        """Load the CUDS objects with the given IRIs.

        Args:
            iris: The IRIs of the CUDS objects to oad.

        Returns:
            Cuds - The CUDS object with the given IRI.
        """
        root_iri = iri_from_uid(self.root)
        zero_iri = iri_from_uid(UUID(int=0))
        iris = map(lambda x: x if x != root_iri else zero_iri, iris)

        for triples, neighbor_triples in self._load_triples_for_iris(*iris):
            triples = self._substitute_zero_iri(triples)
            neighbor_triples = self._substitute_zero_iri(neighbor_triples)
            yield create_from_triples(
                triples=triples,
                neighbor_triples=neighbor_triples,
                session=self,
                fix_neighbors=False,
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

    def _load_triples_for_iris(self, *iris: URIRef):
        """Load the all triples for the CUDS objects with the given IRIs.

        Args:
            iris: The IRIs of the CUDS objects to load the triples for.
        """
        if not iris:
            yield from ()

        try:  # Triples via SPARQL (fast with remote store, only one request).
            query_string_template = f"""
                SELECT ?s ?p ?o ?t WHERE {{
                ?s ?p ?o .
                VALUES ?s {{ %s }}
                OPTIONAL {{ ?o <{RDF.type}> ?t . }}
                }}
            """
            query_result = self._sparql(
                query_string_template % " ".join((f"<{s}>" for s in iris))
            )
            result = dict()
            for row in query_result:
                result[row["s"]] = result.get(row["s"], (set(), set()))
                triples, type_triples_of_neighbors = result[row["s"]]
                triples |= {(row["s"], row["p"], row["o"])}
                if row["t"] is not None:
                    type_triples_of_neighbors |= {
                        (row["o"], RDF.type, row["t"])
                    }
            del query_result
            yield from result.values()
        except NotImplementedError:  # Fall back to triple patterns.
            for iri in iris:
                triples = set(self._triples((iri, None, None)))
                type_triples_of_neighbors = {
                    triple
                    for _, __, o in triples
                    if isinstance(o, URIRef)
                    for triple in self._triples((o, RDF.type, None))
                }
                yield triples, type_triples_of_neighbors
