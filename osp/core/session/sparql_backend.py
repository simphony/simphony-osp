"""Defines an abstract base class for backends that support SPARQL queries."""
from abc import ABC, abstractmethod
import uuid
from osp.core.utils.general import iri_from_uid, uid_from_iri
from osp.core.utils.general import CUDS_IRI_PREFIX


class SPARQLBackend(ABC):
    """Defines an abstract base class for backends that support SPARQL queries.

    Contains only one abstract method, it is feasible to use multiple
    inheritance with this abstract class.
    """

    def sparql(self, query_string):
        """Execute the given SPARQL query on the backend.

        Args:
            query_string (): The SPARQL query as a string.
        """
        return self._sparql(query_string=query_string.replace(
            str(self.root), str(uuid.UUID(int=0))
        ))

    @abstractmethod
    def _sparql(self, query_string):
        """The abstract method performing the query and returning results.

        Args:
            query_string (str): A string with the SPARQL query to perform.

        Returns:
            SparqlResult: A SparqlResult object, which can be iterated to
                obtain he output rows. Then for each `row`, the value for each
                query variable can be retrieved as follows: `row['variable']`.
        """
        pass


class SparqlResult(ABC):
    """A base class for wrapping SPARQL results of different triple stores."""

    def __init__(self, session):
        """Initialize the object."""
        self.session = session

    @abstractmethod
    def close(self):
        """Close the connection."""

    @abstractmethod
    def __iter__(self):
        """Iterate the result."""

    @abstractmethod
    def __len__(self):
        """Return the number of elements in the result."""

    def __enter__(self):
        """Enter the with statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the connection."""
        self.close()


class SparqlBindingSet(ABC):
    """A base class from wrapper rows in SPARQL results."""

    def __init__(self, session):
        """Initialize the object."""
        self.session = session

    @abstractmethod
    def _get(self, variable_name):
        """Get the value of the given variable."""
        pass

    def __getitem__(self, variable_name):
        """Get the value of the given variable.

        Handle wrapper IRIs.
        """
        x = self._get(variable_name)
        if x is not None and x.startswith(CUDS_IRI_PREFIX) \
                and uid_from_iri(x) == uuid.UUID(int=0):
            return iri_from_uid(self.session.root)
        return x
