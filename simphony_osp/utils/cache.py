"""Utilities for caching computations."""

from datetime import datetime
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, Optional, Tuple
from weakref import ref

from simphony_osp.utils.other import take


def lru_cache_weak(
    maxsize: Optional[int] = None, typed: bool = False
) -> Callable:
    """Mimics `functools.lru_cache`, but using a weak reference.

    The motivation behind this decorator is that when `lru_cache` is used
    on an instance method, it keeps the references to `self` that are sent
    to it until the cache is cleared, effectively creating a memory leak.

    Using this decorator instead should prevent the memory leak.
    """

    def decorator(func: Callable):
        @lru_cache(maxsize=maxsize, typed=typed)
        def _cached(_self_weak_ref, *args, **kwargs):
            return func(_self_weak_ref(), *args, **kwargs)

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return _cached(ref(self), *args, **kwargs)

        wrapper.cache_info = _cached.cache_info
        wrapper.cache_clear = _cached.cache_clear
        if hasattr(_cached, "cache_parameters"):
            """The method `cache_parameters` was introduced in Python 3.9."""
            wrapper.cache_parameters = _cached.cache_parameters

        return wrapper

    return decorator


def lru_cache_timestamp(
    read_timestamp: Callable[[Any], datetime],
    maxsize: Optional[int] = None,
    typed: bool = False,
) -> Callable:
    """Like `lru_cache_weak`, but with a timestamp-based cache invalidation.

    The purpose of this decorator is to have a lru-cache decorator that can be
    applied to instance methods whose result depend on a separate object.
    The idea is that when the separate object changes, it can update a
    timestamp stored in itself so that all the cached methods know that they
    need to invalidate the contents of their cache.

    An example of this, and its initial motivation, are ontology classes and
    sessions. The computation of the superclasses of an ontology class
    object is done based on the contents of the graph of the session it is
    attached to. If the session's graph is updated, for example because an
    ontology is installed with pico, the cache should be invalidated. This
    is achieved by updating a timestamp on the session, so that the
    `superclasses` method of each ontology class can compare its own
    timestamp with the session's timestamp, and in this way know that they
    should invalidate their cache.

    Remark: Note that, unlike lru_cache_weak, this decorator keeps an
    independent cache for each value of `self` (that is, for each instance).
    This decision was taken having in mind that each instance can be
    connected to a different external data structure, so having a single
    `lru_cache` would involve that when one of the data structures is modified,
    all the caches are cleared, rather than just the ones related to such data
    structure. Please note that also because of this reason, the real
    maximum size of this cache is `maxsize**2` (`maxsize` instances,
    each one of maximum size `maxsize`). Taking care of this detail was not
    really needed for the use case, so the task was left out.

    Args:
        read_timestamp: A function that retrieves the external timestamp,
            that is, the timestamp of the last cache-invalidating event.
        maxsize: The maximum size of the cache. See the docstring of
            `functools.lru_cache` for more details.
        typed: Whether to cache arguments of different types separately. See
            the docstring of `functools.lru_cache` for more details.
    """

    def decorator(func: Callable):

        holder: Dict[Any, Tuple[datetime, Callable]] = dict()
        """For each instance, holds its timestamp and the cached function."""

        @wraps(func)
        def wrapper(self, *args, **kwargs):

            internal_timestamp, cached_function = holder.get(
                self, (None, None)
            )

            if cached_function is None:
                """Create a cached version of the function for the instance.

                Create a cached version of the function for the given
                instance if none exists yet."""

                internal_timestamp = datetime.now()

                @lru_cache_weak(maxsize=maxsize, typed=typed)
                def cached_function(
                    self_function, *args_function, **kwargs_function
                ):
                    return func(
                        self_function, *args_function, **kwargs_function
                    )

                holder[self] = internal_timestamp, cached_function

            if maxsize is not None:
                # set self as the most recently used item
                try:
                    del holder[self]
                except KeyError:
                    pass
                holder[self] = internal_timestamp, cached_function

                # Remove caches from the holder if there are more instances
                # than the value of the cache size. This is necessary to keep
                # the size of `holder` bounded.
                diff = len(holder) - maxsize
                clear = {item for item in take(holder, diff)}
                for item in clear:
                    del holder[item]

            external_timestamp = read_timestamp(self)
            if external_timestamp and internal_timestamp <= external_timestamp:
                cached_function.cache_clear()
                holder[self] = datetime.now(), cached_function

            return cached_function(self, *args, **kwargs)

        return wrapper

    return decorator
