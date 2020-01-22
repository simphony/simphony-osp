# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.session.buffers import EngineContextIterator


def returns_query_result(func):
    """Decorator to decorate methods that return an iterator of cuds objects.

    :param func: The function to wrap.
    :type func: Callable
    :return: The wrapped function.
    :rtype: Callable
    """
    def f(session, *args, **kwargs):
        iterator = func(session, *args, **kwargs)
        return QueryResult(session, iterator)
    return f


class QueryResult():
    """
    The result of a query in the session
    """

    def __init__(self, session, result_iterator):
        self._iterator = EngineContextIterator(session, result_iterator)
        self._elements = list()

    def __iter__(self):
        yield from self._elements
        for x in self._iterator:
            self._elements.append(x)
            yield x

    def __next__(self):
        x = next(self._iterator)
        self._elements.append(x)
        return x

    def __contains__(self, other):
        return other in self.all()

    def all(self):
        """Returns all the elements in the result

        :return: A list containing all elements in the result.
        :rtype: List[Cuds]
        """
        self._elements += list(self._iterator)
        return self._elements

    def first(self):
        """Return the first element in the result

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

        :param raise_result_empty_error: Whether to raise an error
            if result is empty
        :type  raise_result_empty_error: bool
        :raises MultipleResultsError: The result consists of multiple elements
        :raises ResultEmptyError: The result is empty
        :return: The single element of the result
        :rtype: Cuds
        """
        x = self.first()
        if len(self._elements) > 1:
            raise MultipleResultsError(
                "Found %s result elements" % len(self.all()))
        try:
            x = next(self._iterator)
            self._elements.append(x)
            raise MultipleResultsError(
                "Found %s result elements" % len(self.all()))
        except StopIteration:
            pass
        if x is None and raise_result_empty_error:
            raise ResultEmptyError
        return x


class ResultEmptyError(Exception):
    pass


class MultipleResultsError(Exception):
    pass
