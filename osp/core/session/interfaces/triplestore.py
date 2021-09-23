"""A session connecting to a backend which stores the CUDS in triples."""

from abc import ABC, abstractmethod
from typing import Iterable, Iterator, Union, Optional, TYPE_CHECKING

from osp.core.ontology.datatypes import Pattern, Triple, UID
from osp.core.session.interfaces.interface import Interface, InterfaceStore

if TYPE_CHECKING:
    from osp.core.ontology import OntologyEntity


class TriplestoreStore(InterfaceStore):
    """RDFLib store, communicates with the TripleStoreInterface."""

    transaction_aware = True

    _interface: "TriplestoreInterface"

    def __init__(self, *args, interface=None, **kwargs):
        if interface is None:
            raise ValueError(f"No interface provided.")
        if not isinstance(interface, Interface):
            raise TypeError(
                f"Object provided as interface is not a Wrapper.")
        # TODO: Do not create the buffers in the first place.
        super().__init__(*args, interface=interface, **kwargs)
        del self._buffers

    def add(self, triple, context, quoted=False):
        self._interface.add(triple)

    def remove(self, triple_pattern, context=None):
        self._interface.remove(triple_pattern)

    def triples(self, triple_pattern, context=None):
        for triple in self._interface.triples(triple_pattern):
            yield triple, iter(())

    def commit(self):
        self._interface.commit()

    def rollback(self):
        self._interface.rollback()


class TriplestoreInterface(Interface):
    """A session connecting to a backend which stores the CUDS in triples."""

    store_class = TriplestoreStore

    @abstractmethod
    def triples(self, pattern: Pattern) -> Iterator[Triple]:
        pass

    @abstractmethod
    def add(self, *triples: Triple) -> Iterator[Triple]:
        pass

    @abstractmethod
    def remove(self, pattern: Pattern) -> Iterator[Triple]:
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass

    def open(self, configuration: str):
        pass

    def apply_added(self, entity: "OntologyEntity") -> None:
        self.add(*entity.triples)

    def apply_updated(self, entity: "OntologyEntity") -> None:
        self.remove((entity.identifier, None, None))
        self.add(*entity.triples)

    def apply_deleted(self, entity: "OntologyEntity") -> None:
        self.remove((entity.identifier, None, None))

    def _load_from_backend(self, uid: UID) \
            -> Optional["OntologyEntity"]:
        raise NotImplementedError

    def close(self):
        pass
