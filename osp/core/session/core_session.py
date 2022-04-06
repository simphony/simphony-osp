"""The core session used as default when no backend is connected."""
import logging

from .session import Session
from .sparql_backend import SPARQLBackend, SparqlBindingSet, SparqlResult

logger = logging.getLogger(__name__)


class CoreSession(Session, SPARQLBackend):
    """Core default session for all objects."""

    _warned_sparql_slow = False

    def __str__(self):
        """Convert the core session object to string."""
        return "<CoreSession object>"

    # OVERRIDE
    def _notify_update(self, cuds_object):
        pass

    # OVERRIDE
    def _notify_delete(self, cuds_object):
        pass

    # OVERRIDE
    def _notify_read(self, cuds_object):
        pass

    def _get_full_graph(self):
        """Get the triples in the core session."""
        return self.graph

    def _sparql(self, query_string):
        """Execute the given SPARQL query on the graph of the core session.

        Args:
            query_string (str): The SPARQL query as a string.
        """
        if not CoreSession._warned_sparql_slow:
            logger.warning(
                "At the moment, SPARQL queries on the default "
                "session of OSP-core (the core session) are "
                "supported, but slow. For better performance, "
                "please perform the query on another session with "
                "SPARQL support (e.g. a triple store wrapper)."
            )
            CoreSession._warned_sparql_slow = True
        result = self.graph.query(query_string)
        return CoreSession.CoreSessionSparqlResult(result, self)

    class CoreSessionSparqlResult(SparqlResult):
        """The result of a SPARQL query on the core session."""

        def __init__(self, query_result, session):
            """Initialize the result."""
            self.result = query_result
            super().__init__(session)

        def close(self):
            """Close the connection."""
            pass

        def __iter__(self):
            """Iterate the result."""
            for row in self.result:
                yield CoreSession.CoreSessionSparqlBindingSet(
                    row, self.session
                )

        def __len__(self):
            """Compute the number of elements in the result."""
            return len(self.result)

    class CoreSessionSparqlBindingSet(SparqlBindingSet):
        """A row in the result. Mapping from variable to value."""

        def __init__(self, row, session):
            """Initialize the row."""
            self.binding_set = row
            super().__init__(session)

        def _get(self, variable_name):
            return self.binding_set[variable_name]


core_session = CoreSession()
