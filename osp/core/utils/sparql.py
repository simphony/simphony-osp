"""A tool to perform SPARQL queries."""

from typing import TYPE_CHECKING

from rdflib.query import Result

from osp.core.ontology.individual import OntologyIndividual

if TYPE_CHECKING:
    from osp.core.session import Session


class SparqlResultRow:
    """A base class from wrapper rows in SPARQL results."""

    def __init__(self,
                 session: 'Session',
                 rdflib_row,
                 datatypes=None):
        """Initialize the object."""
        self.session = session
        self.datatypes = datatypes or dict()
        self._rdflib_row = rdflib_row

    def __getitem__(self, variable_name):
        """Get the value of the given variable.

        Handles wrapper IRIs and datatype conversion.
        """
        result = self._rdflib_row[variable_name]
        return self._check_datatype(variable_name, result)

    def _check_datatype(self, variable_name, result):
        """Check if result shall be converted to a certain datatype.

        The `variable_name` is checked against the dictionary `self.datatypes`,
        and if a datatype is defined there for such variable name, then the
        function returns the value of the variable converted to such datatype.

        Args:
            variable_name (str): the variable of the SPARQL query on which the
                check should be performed.
            result (Union[URIRef, Literal]): a result returned by the SPARQL
                query for such variable name. This is what is then converted
                to the desired datatype.

        Returns:
            Any: the result of the SPARQL query converted to the desired
                datatype.

        Raises:
            TypeError: when an invalid string is specified as target
                datatype or the target datatype is neither a string nor a
                callable.

            ValueError: when there is an exception on the conversion process.
        """
        if result is None or not self.datatypes:
            return result
        variable_type = self.datatypes.get(variable_name)
        if variable_type is None:
            return result

        unknown_type_error = TypeError(f"Variable type {variable_type} not "
                                       f"understood.")
        try:
            if variable_type == OntologyIndividual:
                try:
                    individual = self.session.from_identifier(result)
                except KeyError:
                    individual = None
                return individual
            elif callable(variable_type):
                return variable_type(result)
            else:
                raise unknown_type_error
        except Exception as exception:
            if exception is not unknown_type_error:
                raise ValueError(exception) from exception
            else:
                raise unknown_type_error


class SparqlResult:
    """A base class for wrapping SPARQL results of different triple stores."""

    def __init__(self,
                 session: 'Session',
                 rdflib_result: Result):
        """Initialize the object."""
        self.session = session
        self._rdflib_result = rdflib_result

    def __iter__(self):
        """Iterate the result."""
        for x in self._rdflib_result:
            yield SparqlResultRow(session=self.session,
                                  rdflib_row=x)

    def __len__(self):
        """Return the number of elements in the result."""
        return len(self._rdflib_result)

    def __enter__(self):
        """Enter the with statement."""
        return self

    def __call__(self, **kwargs):
        """Add kwargs to datatypes when class is called."""
        # Set the datatypes of each returned SparqlBindingSet while keeping
        # __iter__ as an abstract method.
        for x in self._rdflib_result:
            yield SparqlResultRow(session=self.session,
                                  rdflib_row=x,
                                  datatypes=kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the connection."""
        # return super().__exit__(exc_type, exc_val, exc_tb)
        pass
