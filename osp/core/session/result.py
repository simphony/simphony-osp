"""Provide a nice API for query results."""

from osp.core.session.buffers import EngineContextIterator


def returns_query_result(func):
    """Decorate methods that return an iterator of cuds objects.

    Args:
        func (Callable): The function to wrap.

    Returns:
        Callable: The wrapped function.
    """

    def f(session, *args, **kwargs):
        iterator = func(session, *args, **kwargs)
        return QueryResult(session, iterator)

    return f


class QueryResult:
    """The result of a query in the session."""

    def __init__(self, session, result_iterator):
        """Initialize the iterator.

        Args:
            session (Session): The session where the query was executed.
            result_iterator (Iterator): An iterator over the results.
        """
        self._iterator = EngineContextIterator(session, result_iterator)
        self._elements = list()

    def __iter__(self):
        """Return an iterator over the results.

        Yields:
            Cuds: The objects in the result.
        """
        yield from self._elements
        for x in self._iterator:
            self._elements.append(x)
            yield x

    def __next__(self):
        """Get the next element in the result.

        Returns:
            Cuds: The next element.
        """
        x = next(self._iterator)
        self._elements.append(x)
        return x

    def __contains__(self, other):
        """Check if an object is part of this result.

        Args:
            other (Cuds): The object to check.

        Returns:
            bool: Whether the result contains the given object,
        """
        return other in self.all()

    def all(self):
        """Return all the elements in the result.

        :return: A list containing all elements in the result.
        :rtype: List[Cuds]
        """
        self._elements += list(self._iterator)
        return self._elements

    def first(self):
        """Return the first element in the result.

        :return: The first element in the result
        :rtype: Cuds
        """
        if not self._elements:
            try:
                self._elements.append(next(self._iterator))
            except StopIteration:
                return None
        return self._elements[0]

    def one(self, raise_result_empty_error=True):
        """Get the first element in the result.

        Raise an error if
        1. The result contains more than one element
        2. The result does not contain any element

        Args:
            raise_result_empty_error (bool, optional): Whether to raise an
                error if result is empty. Defaults to True.

        Raises:
            MultipleResultsError: The result consists of multiple elements.
            ResultEmptyError: The result is empty.

        Returns:
            Cuds: The single element of the result
        """
        x = self.first()
        if len(self._elements) > 1:
            raise MultipleResultsError(
                "Found %s result elements" % len(self.all())
            )
        try:
            x = next(self._iterator)
            self._elements.append(x)
            raise MultipleResultsError(
                "Found %s result elements" % len(self.all())
            )
        except StopIteration:
            pass
        if x is None and raise_result_empty_error:
            raise ResultEmptyError
        return x


class ResultEmptyError(Exception):
    """The result is unexpectedly empty."""


class MultipleResultsError(Exception):
    """Only a single result is expected, but there were multiple."""
