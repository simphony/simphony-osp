from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Type, Union

from .session import Session

from osp.core.session.interfaces.interface import Interface

if TYPE_CHECKING:
    from osp.core.session.session import Session


class Wrapper(ABC, Session):

    def __init__(self,
                 *args,
                 ontology: Optional[Union[Session, bool]] = None,
                 **kwargs):
        interface_instance = self._interface(*args,
                                             **kwargs)
        store = self._interface.store_class(
            interface=interface_instance)
        super().__init__(store=store,
                         ontology=ontology)

    @property
    @abstractmethod
    def _interface(self) -> Type[Interface]:
        pass
