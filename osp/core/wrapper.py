"""A user-facing class creating a session using a specific interface."""

from abc import ABC, abstractmethod
from typing import Optional, Set, Type, Union

from rdflib.term import Identifier

from osp.core.session import Session
from osp.core.ontology.entity import OntologyEntity
from osp.core.interfaces.interface import Interface
from osp.core.utils.datatypes import UID


class Wrapper:
    """A user-facing class for managing a session.

    The idea is to create hybrid subclasses from this class, for example
    ontology entities that are also able to manage sessions.

    Anything that has a `_session` attribute may be used to manage a session.
    """

    # Any class combined with the wrapper is expected to provide the two
    # properties below.
    session: Session
    _session: Session

    def __enter__(self):
        """Enter the associated session's context."""
        self._session.__enter__()
        return self

    def __exit__(self, *args):
        """Exit the associated session's context."""
        self._session.__exit__(*args)

    def commit(self) -> None:
        """Commit the changes made to the backend."""
        return self._session.commit()

    def close(self) -> None:
        """Close the connection to the backend."""
        return self._session.close()


class WrapperSpawner(ABC, Wrapper):
    """A user-facing class for spawning a session."""

    @classmethod
    @abstractmethod
    def _get_interface(cls) -> Type[Interface]:
        """The type of interface that the instantiated session will use."""
        pass

    def __new__(cls,
                configuration_string: str = '',
                *args,
                ontology: Optional[Union[Session, bool]] = None,
                root: Optional[Union[str,
                                     Identifier,
                                     'OntologyEntity']] = None,
                **kwargs) -> Union['WrapperSpawner', OntologyEntity]:
        """Initialize the session using the wrapper's interface type.

        Creates an interface and a store using that interface. Then
        initialize the session using such store.
        """
        interface_class = cls._get_interface()
        if all(x is not None for x in (root, interface_class.root)):
            raise ValueError("This Wrapper has a fixed root ontology "
                             "entity, which can not be changed.")
        root = interface_class.root or root

        # Initialize the session.
        interface_instance = interface_class(configuration_string,
                                             *args,
                                             **kwargs)
        store = cls._get_interface().store_class(interface=interface_instance)
        store.open(configuration_string)
        session = Session(store=store, ontology=ontology)

        # Decide whether to return the WrapperSpawner or a WrappingEntity.
        if root is None:
            wrapper = super(WrapperSpawner, cls).__new__(cls)
            wrapper._session = session
            return wrapper
        else:
            if isinstance(root, OntologyEntity):
                session.update(root)
                class_ = root.__class__
                uid = UID(root.identifier)
            else:
                class_ = session.from_identifier(root).__class__
                uid = UID(root)
            class_ = type(f"Wrapping{class_.__name__}",
                          (class_, Wrapper),
                          {})
            entity = class_(uid=uid, session=session, merge=True)
            return entity

    @property
    def session(self) -> Session:
        """Returns the session that the wrapper is connected to."""
        return self._session

    def add(self, *other: OntologyEntity):
        """Add an item to the session connected to the wrapper."""
        for entity in other:
            self._session.update(entity)

    def delete(self, *other: OntologyEntity):
        """Remove an item from the session connected to the wrapper."""
        for entity in other:
            self._session.delete(entity)

    def __contains__(self, item: OntologyEntity):
        """Determine whether an entity is contained in the wrapper session."""
        return item in self._session

    def __iter__(self):
        """Iterate over all the entities in the wrapper's session.

        This operation can be computationally VERY expensive.
        """
        return self._session.__iter__()

    def __len__(self):
        """Calculate the number of entities in the bag's session.

        This operation can be computationally VERY expensive.
        """
        return sum(1 for _ in self)

    def from_identifier(self, identifier: Identifier) -> OntologyEntity:
        """Get an entity from its identifier."""
        return self._session.from_identifier(identifier)

    def from_label(self,
                   label: str,
                   lang: Optional[str] = None,
                   case_sensitive: bool = False) -> Set[OntologyEntity]:
        """Get an ontology entity from the session by label."""
        return self._session.from_label(label, lang, case_sensitive)
