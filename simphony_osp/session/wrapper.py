"""A user-facing class creating a session using a specific interface."""

from abc import ABC, abstractmethod
from typing import Iterable, Optional, Type, Union

from rdflib import Graph

from simphony_osp.interfaces.interface import Interface, InterfaceDriver
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.operations.container import Container
from simphony_osp.session.session import Session


class Wrapper:
    """A user-facing class for managing a session.

    The idea is to create hybrid subclasses from this class, for example
    ontology entities that are also able to manage sessions.

    Anything that has a `_session` attribute may be used to manage a session.
    """

    # Any class combined with the wrapper is expected to provide the two
    # properties below.
    session: Session
    interface: Optional[Interface] = None
    _session: Session
    _exit_container: bool = False

    def __enter__(self):
        """Enter the associated session's context."""
        self._session.__enter__()
        if isinstance(self, Container):
            Container.__enter__(self)
        return self

    def __exit__(self, *args):
        """Exit the associated session's context."""
        if isinstance(self, Container):
            self._exit_container = True
            Container.__exit__(self, *args)
            self._exit_container = False
        self._session.__exit__(*args)

    def commit(self) -> None:
        """Commit the changes made to the backend."""
        return self._session.commit()

    def close(self) -> None:
        """Close the connection to the backend."""
        if isinstance(self, Container):
            Container.close(self)
        if not self._exit_container:
            return self._session.close()

    def delete(self, *entities: OntologyEntity) -> None:
        """Delete entities from the backend."""
        for entity in entities:
            self._session.delete(entity)

    def compute(self, *args, **kwargs) -> None:
        """Instructs the backend to run a simulation if supported."""
        return self._session.compute(*args, **kwargs)


class WrapperSpawner(ABC, Session):
    """A user-facing class for spawning a session."""

    @classmethod
    @abstractmethod
    def _get_interface(cls) -> Type[Interface]:
        """The type of interface that the instantiated session will use."""
        pass

    def __new__(
        cls,
        configuration_string: str = "",
        create: bool = False,
        ontology: Optional[Union[Session, bool]] = None,
        **kwargs: Union[
            str,
            int,
            float,
            bool,
            None,
            Iterable[Union[str, int, float, bool, None]],
        ]
    ) -> Session:
        """Initialize the session using the wrapper's interface type.

        Creates an interface and a store using that interface. Then
        initialize the session using such store.
        """
        interface_class = cls._get_interface()
        interface_instance = interface_class(**kwargs)
        store = InterfaceDriver(interface=interface_instance)
        graph = Graph(store=store)
        graph.open(configuration_string, create=create)
        session = Session(base=graph, driver=store, ontology=ontology)
        session._driver = store
        return session
