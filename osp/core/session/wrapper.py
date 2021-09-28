"""A user-facing class creating a session using a specific interface."""

from abc import ABC, abstractmethod
from typing import Optional, Set, Type, TYPE_CHECKING, Union

from rdflib.term import Identifier

from .session import Session
from osp.core.ontology.datatypes import UID
from osp.core.ontology.interactive.container import Container
from osp.core.session.interfaces.interface import Interface

if TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity
    from osp.core.ontology.individual import OntologyIndividual


class Wrapper(ABC):
    """A user-facing class for managing a session."""

    # Public API
    # ↓ ------ ↓

    @property
    def session(self) -> Session:
        """Returns the session connected to the wrapper."""
        return self._session

    def from_identifier(self, identifier: Identifier) -> 'OntologyEntity':
        """Get an entity from its identifier."""
        return self._session.from_identifier(identifier)

    def from_label(self,
                   label: str,
                   lang: Optional[str] = None,
                   case_sensitive: bool = False) -> Set['OntologyEntity']:
        """Get an ontology entity from the session by label."""
        return self._session.from_label(label, lang, case_sensitive)

    def commit(self) -> None:
        """Commit the changes made to the wrapper."""
        return self._session.commit()

    def close(self):
        """Close the connection to the backend."""
        self.container.close()
        self._session.close()

    def __enter__(self):
        """Enter the wrapper's context."""
        self._session.__enter__()
        self.container.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the wrapper's context."""
        self.container.__exit__(exc_type, exc_val, exc_tb)
        self._session.__exit__(exc_type, exc_val, exc_tb)
        self.close()

    def add(self, *individuals: 'OntologyIndividual'):
        """Add an element to the wrapper."""
        self.container.add(*individuals)

    def remove(self, *individuals: 'OntologyIndividual'):
        """Remove an element from the wrapper."""
        self.container.remove(*individuals)

    def __iter__(self):
        """Yields entities from the wrapper."""
        yield from self.container.__iter__()

    def __contains__(self, item: 'OntologyIndividual'):
        """Determines whether an entity is contained in the wrapper."""
        return self.container.__contains__(item)

    def __len__(self):
        """Returns the number of elements in the wrapper."""
        return self.container.__len__()

    # ↑ ------ ↑
    # Public API

    container: Container = None
    _session: Session = None

    @property
    @abstractmethod
    def _interface(self) -> Type[Interface]:
        """The type of interface that the instantiated session will use."""
        pass

    def __init__(self,
                 *args,
                 ontology: Optional[Union[Session, bool]] = None,
                 **kwargs):
        """Initialize the session using the wrapper's interface type.

        Creates an interface and a store using that interface. Then
        initialize the session using such store.
        """
        # Initialize the session.
        interface_instance = self._interface(*args,
                                             **kwargs)
        store = self._interface.store_class(
            interface=interface_instance)
        self._session = Session(store=store, ontology=ontology)

        # Initialize the container.
        self.container = Container(uid=UID(0),
                                   session=self._session,
                                   merge=True)
        self.container.opens_in = self._session
        self.container.open()
        # -> Container must be closed when 'wrapper' is closed.
