from enum import IntEnum
from contextlib import nullcontext


class BufferType(IntEnum):
    ADDED = 0
    UPDATED = 1
    DELETED = 2


class BufferContext(IntEnum):
    USER = 0
    ENGINE = 1


class EngineContext():
    def __init__(self, session):
        self._session = session

    def __enter__(self):
        if not hasattr(self._session, "_current_context"):
            return
        self._prev_ = self._session._current_context
        if self._prev_ != BufferContext.ENGINE:
            self._session._reset_buffers(BufferContext.ENGINE)
        self._session._current_context = BufferContext.ENGINE

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not hasattr(self._session, "_current_context"):
            return
        self._session._current_context = self._prev_


class EngineContextIterator():
    def __init__(self, session, iterator):
        self._session = session
        self._iterator = iter(iterator)

    def __next__(self):
        with EngineContext(self._session):
            return next(self._iterator)

    def __iter__(self):
        return self


def get_buffer_context_mngr(session, buffer_context):
    if buffer_context == BufferContext.ENGINE:
        return EngineContext(session)
    return nullcontext()
