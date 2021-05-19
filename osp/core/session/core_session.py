"""The core session used as default when no backend is connected."""
from .session import Session
from .db.triplestore_wrapper_session import SparqlResult, SparqlBindingSet


class CoreSession(Session):
    """Core default session for all objects."""

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

    def sparql(self, query_string):
        """Execute the given SPARQL query on the graph of the core session.

        Args:
            query_string (str): The SPARQL query as a string.
        """
        # TODO: raise slowness warning.
        result = self.graph.query(query_string)
        return CoreSession.CoreSessionSparqlResult(result, self)

    class CoreSessionSparqlResult(SparqlResult):
        """The result of a SPARQL query of an AGraph session."""

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
                yield CoreSession.CoreSessionSparqlBindingSet(row,
                                                              self.session)

        def __len__(self):
            """Compute the number of elements in the result."""
            # TODO: make sure it works.
            return len(self.result)

    class CoreSessionSparqlBindingSet(SparqlBindingSet):
        """A row in the result. Mapping from variable to value."""

        def __init__(self, row, session):
            """Initialize the row."""
            self.binding_set = row
            super().__init__(session)

        def _get(self, variable_name):
            return self.binding_set[variable_name]
