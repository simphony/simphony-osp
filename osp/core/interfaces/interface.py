"""An Interface represents an interface between OSP-core and other software."""

from abc import ABC
from enum import IntEnum
from typing import Optional, Type

from rdflib.store import Store
from rdflib.term import Identifier

__all__ = ['Interface', 'BufferType']


class BufferType(IntEnum):
    """The two types of buffers.

    - ADDED: For triples that have been added.
    - DELETED: For triples that have been deleted.
    """

    ADDED = 0
    DELETED = 1


class Driver(Store):

    def __init__(self,
                 *args,
                 interface: 'Interface',
                 **kwargs):
        super().__init__(*args, **kwargs)


class Interface:
    """Class representing an interface between OSP-core and other software."""

    # Definition of:
    #   Interface
    # ↓ ---------- ↓

    root: Optional[Identifier] = None

    # ↑ ------------ ↑
    # Definition of:
    #   Interface

    driver: Type[Driver]
