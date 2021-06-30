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
        # NOTE: Why is the uid of the root replaced in the query?
        #  Each time that a session is opened, the user is expected to create a
        #  wrapper for the session. The uid of the wrapper is new each time it
        #  is created. Thus, the uid saved to the database does not match the
        #  uuid of the new wrapper, so the objects in the database become
        #  unreachable. As a workaround, OSP-core is replacing the uid of the
        #  wrapper with zero, so that the root of the session always has the
        #  same uid and the CUDS objects are reachable from the root. This is
        #  done not only here, but also on other parts of the code.

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
        self.datatypes = SparqlDataTypes()

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

    def __call__(self, **kwargs):
        """Add kwargs to datatypes when class is called."""
        self.datatypes.update(kwargs)
        return self.__iter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the connection."""
        self.close()


class SparqlBindingSet(ABC):
    """A base class from wrapper rows in SPARQL results."""

    def __init__(self, session, datatypes=None):
        """Initialize the object."""
        self.session = session
        self.datatypes = datatypes or SparqlDataTypes()

    @abstractmethod
    def _get(self, variable_name):
        """Get the value of the given variable."""
        pass

    def __getitem__(self, variable_name):
        """Get the value of the given variable.

        Handle wrapper IRIs.
        """
        iri = self._get(variable_name)
        if iri is not None and iri.startswith(CUDS_IRI_PREFIX) \
                and uid_from_iri(iri) == uuid.UUID(int=0):
            iri = iri_from_uid(self.session.root)
        return self._check_datatype(variable_name, iri)

    def _check_datatype(self, variable_name, iri):
        """Check if iri shall be converted to a certain datatype."""
        try:
            variable_type = self.datatypes[variable_name]
            if variable_type == 'cuds':
                cuds_query = self.session.load_from_iri(iri)
                return cuds_query.first()
            elif variable_type in [float, str, int, bool]:
                return variable_type(iri._value)
            elif callable(variable_type):
                return variable_type(iri)
            else:
                raise TypeError("Variable type not understood")
        except KeyError:
            return iri
        except Exception as excep:
            raise ValueError(excep)


class SparqlDataTypes(dict):
    """Class in order to store the desired datatypes."""
    def __init__(self, **kwargs):
        """Initialize the object."""
        super().__init__(kwargs)
