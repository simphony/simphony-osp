from enum import IntEnum


class BufferType(IntEnum):
    ADDED = 0
    UPDATED = 1
    DELETED = 2


class BufferOperator(IntEnum):
    USER = 0
    ENGINE = 1


class OperatorEngine():
    def __init__(self, session):
        self._session = session

    def __enter__(self):
        if not hasattr(self._session, "_current_operator"):
            return
        self._prev_operator = self._session._current_operator
        if self._prev_operator != BufferOperator.ENGINE:
            self._session._reset_buffers(operator=BufferOperator.ENGINE)
        self._session._current_operator = BufferOperator.ENGINE

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not hasattr(self._session, "_current_operator"):
            return
        self._session._current_operator = self._prev_operator


class OperatorEngineIterator():
    def __init__(self, session, iterator):
        self._session = session
        self._iterator = iter(iterator)

    def __next__(self):
        with OperatorEngine(self._session):
            return next(self._iterator)

    def __iter__(self):
        return self
