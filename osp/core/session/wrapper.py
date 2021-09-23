"""A user-facing class creating a session using a specific interface."""

from abc import ABC, abstractmethod
from typing import Optional, Type, Union

from .session import Session

from osp.core.session.interfaces.interface import Interface


class Wrapper(ABC, Session):
    """A user-facing class creating a session using a specific interface."""

    def __init__(self,
                 *args,
                 ontology: Optional[Union[Session, bool]] = None,
                 **kwargs):
        """Initialize the session using the wrapper's interface type.

        Creates an interface and a store using that interface. Then
        initialize the session using such store.
        """
        interface_instance = self._interface(*args,
                                             **kwargs)
        store = self._interface.store_class(
            interface=interface_instance)
        super().__init__(store=store,
                         ontology=ontology)

    @property
    @abstractmethod
    def _interface(self) -> Type[Interface]:
        """The type of interface that the instantiated session will use."""
        pass
