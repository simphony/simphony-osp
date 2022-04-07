"""Buffers are used to collect changes of the user or the engine.

There are six buffers in total. Three for the user and three for the engine.
This file defines useful Enums and contextmanager that can indicate
which buffer should be modified.
"""

from enum import IntEnum

try:
    from contextlib import nullcontext
except Exception:  # Python <= 3.6

    class nullcontext:
        """ContextManager that does nothing."""

        def __enter__(self):
            """Do nothing."""
            pass

        def __exit__(self, *args, **kwargs):
            """Do nothing."""
            pass


class BufferType(IntEnum):
    """The three types of buffers.

    - ADDED: For objects that have been added.
    - UPDATED: For objects that have been updated.
    . DELETED: For objects that have been deleted.
    """

    ADDED = 0
    UPDATED = 1
    DELETED = 2


class BufferContext(IntEnum):
    """The BufferContext specifies who is modifying the buffers at the moment.

    There are two BufferContexts:
    - USER: The user is creating objects and modifying the buffers.
    - ENGINE: Objects are loaded from the engine.
        The engine modifies the buffers.

    There are separate buffers for each buffer context.
    E.g. In the ENGINE Buffer Context only the buffer of the engine is
    modified.
    """

    USER = 0
    ENGINE = 1


class EngineContext:
    """A context Manager used to switch to the Engine Buffer Context."""

    def __init__(self, session):
        """Initialize the Context Manager.

        Args:
            session (Session): The session that should switch the buffer
                context.
        """
        self._session = session

    def __enter__(self):
        """Enter the Engine Buffer Context."""
        if not hasattr(self._session, "_current_context"):
            return
        self._prev_ = self._session._current_context
        if self._prev_ != BufferContext.ENGINE:
            self._session._reset_buffers(BufferContext.ENGINE)
        self._session._current_context = BufferContext.ENGINE

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the Engine Buffer Context."""
        if not hasattr(self._session, "_current_context"):
            return
        self._session._current_context = self._prev_


class EngineContextIterator:
    """Enters the Engine BufferContext when an element is returned."""

    def __init__(self, session, iterator):
        """Initialize the iterator.

        Args:
            session (Session): The session that owns the elements in the
                iterator.
            iterator (Iterator[Cuds]): An iterator over CUDS objects.
        """
        self._session = session
        self._iterator = iter(iterator)

    def __next__(self):
        """Enter the buffer context when returning the next element.

        Returns:
            Cuds: The next element in the iterator.
        """
        with EngineContext(self._session):
            return next(self._iterator)

    def __iter__(self):
        """As this is already an iterator, return self.

        Returns:
            Iterator: self.
        """
        return self


def get_buffer_context_mngr(session, buffer_context):
    """Get a context manager for the given engine.

    Args:
        session (Session): The session to use the context manager for.
        buffer_context (BufferContext): The BufferContext to enter with
            with the context manager.

    Returns:
        ConextManager: A ContextManager that enters the given BufferContext.
    """
    if buffer_context == BufferContext.ENGINE:
        return EngineContext(session)
    return nullcontext()
