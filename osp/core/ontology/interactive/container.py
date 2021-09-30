"""Special kind of ontology individual designed to organize entities."""

import logging
from typing import (Dict, Iterable, Iterator, List, Optional, TYPE_CHECKING,
                    Tuple, Union)
from weakref import ReferenceType, ref

from rdflib import URIRef

from osp.core.namespaces import cuba
from osp.core.ontology.datatypes import UID, RDFCompatibleType, Triple
from osp.core.ontology.individual import OntologyIndividual
from osp.core.session.session import Session

if TYPE_CHECKING:
    from osp.core.ontology.attribute import OntologyAttribute

logger = logging.getLogger(__name__)


class Container(OntologyIndividual):
    """Special kind of ontology individual designed to organize entities."""

    @classmethod
    def get_current_container_context(cls) -> Optional['Container']:
        """Returns the most recently opened container (if any is open).

        When no container is currently opened, it returns none.
        """
        return cls._container_contexts[-1] \
            if len(cls._container_contexts) > 0 else None

    def __init__(self,
                 uid: Optional[UID] = None,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 attributes: Optional[
                     Dict['OntologyAttribute',
                          Iterable[RDFCompatibleType]]] = None,
                 merge: bool = False,
                 ) -> None:
        """Initialize the container."""
        super().__init__(uid=uid,
                         session=session,
                         triples=triples,
                         class_=cuba.Container,
                         attributes=attributes,
                         merge=merge,
                         )
        logger.debug("Instantiated container %s" % self)

    @property
    def opens_in(self) -> Optional[Union['Container', Session, URIRef]]:
        """Returns where the container opens by default.

        Returns the session or container in which the container opens by
        default.

        This is NOT the session where the container is stored. The
        ontological data defining the container can be stored in ANY
        session, just like any other ontology individual.
        """
        if isinstance(self._opens_in, ref):
            return self._opens_in()
        else:
            for i in range(1, len(self._container_contexts) + 1):
                container = self._container_contexts[-i]
                if container.iri == self._opens_in:
                    return container
            else:
                return self._opens_in

    @opens_in.setter
    def opens_in(self,
                 value: Optional[Union['Container', Session]] = None) \
            -> None:
        """Sets where the container opens by default.

        Sets the session or container in which the container opens by
        default.
        """
        if isinstance(value, Session) and not isinstance(value, Container):
            self._opens_in = ref(value)
        elif isinstance(value, Container):
            self._opens_in = value.iri
        elif value is None:
            self._opens_in = value
        else:
            raise TypeError(f"Expected {Container} or {Session}, got "
                            f"{type(value)}.")

    _opens_in: Optional[
        Union[
            ReferenceType,
            URIRef]] = None
    """Where the container opens by default.

    Optional[Union[ReferenceType[Session], URIRef]]
    """

    @property
    def session_linked(self) -> Optional[Session]:
        """Returns session that the container uses to fetch items from."""
        return self._session_linked

    _session_linked: Optional[Session] = None
    """The session that the container uses to fetch items from."""

    @property
    def is_open(self) -> bool:
        """Returns the current status of the container.

        - Derived from the `_container_contexts` stack. If the container is
          there, then it is open.
        """
        return self in self._container_contexts

    # Methods that do NOT require the container to be open.
    # -------------------------------------------------------------------------

    @property
    def references(self) -> Tuple[URIRef, ...]:
        """Returns a list of the IRIs of all linked individuals.

        - This works without opening the container (checks the linked
          individuals).

        """
        return tuple(self._session.graph.objects(self.identifier,
                                                 cuba.contains.iri))

    @references.setter
    def references(self, value: Iterable[URIRef]):
        """Replace the current linked individuals with the ones received.

        - This works without opening the container.
        """
        provided = set(value)
        existing = set(self._session.graph.objects(self.identifier,
                                                   cuba.contains.iri))
        add = provided - existing
        remove = existing - provided
        for iri in remove:
            self._session.graph.remove((self.identifier, cuba.contains.iri,
                                        iri))
        for iri in add:
            self._session.graph.add((self.identifier, cuba.contains.iri, iri))

    @property
    def num_references(self) -> int:
        """Returns the number of connected individuals.

        - Does NOT need the container to be open to operate.
        """
        return len(set(self._session.graph.objects(self.identifier,
                                                   cuba.contains.iri)))

    def open(self,
             environment: Optional[Union[Session,
                                         'Container']] = None) -> None:
        """Opens the container in `environment`.

        Relevant when an individual needs to be fetched, added
        or removed.

        - PREVENT OPENING CONTAINER IN ITSELF.

        - DO NOT OPEN IF ALREADY OPEN.

        # Issue: session and container stacks need to be mixed somehow
        # (handled later).

        - If no environment (session or container) is provided:
            - Try to open in `opens_in` if not None.
            - Otherwise, try to open in the current container context (if
              exists, the last element of the context list). Beware that the
              `linked_session` of the container context needs to match the
              current default session. Otherwise we changed the default
              session, and we need to open in the default session instead.
            - Otherwise, try to open in the default session (Cuds._session).

        - If opening in a session:
            - Fails (raise RuntimeError) if such session is closed.
            - Changes `_session_linked` to the provided session.
            - Pushes self to the context stack.
        - If opening in a container:
            - If not open, open such container without arguments.
            - Change `_session_linked` to such container's `session_linked`
               attribute.
            - Push self to the context stack.

        - Only really safe in a single threaded program.
        - What happens if the user closes the session within a container?
        """
        if environment is None:
            if self.opens_in is None:
                # Try to open in current container context.
                try:
                    environment = self._container_contexts[-1]
                except IndexError:
                    # No container context, use default session.
                    environment = Session.get_default_session()
            else:
                environment = self.opens_in

        if isinstance(environment, Session):
            if False:  # (session_closed) TODO: session should report this.
                raise RuntimeError(f'Cannot open container {self} in closed '
                                   f'session {environment}.')
            if self.is_open and environment is not self._session_linked:
                raise RuntimeError(f'Attempted to open container {self} in '
                                   f'session {environment}, but the '
                                   f'has been already opened in '
                                   f'{self._session_linked}. Please, '
                                   f'close the container first.')
            self._session_linked = environment
            self._container_contexts.append(self)
        elif isinstance(environment, Container):
            if self.is_open and \
                    self._session_linked is not environment._session_linked:
                raise RuntimeError(f'Attempted to open container {self} in '
                                   f'container {environment}, which is '
                                   f'linked to session '
                                   f'{environment._session_linked} '
                                   f'different from '
                                   f'{self._session_linked} in which this '
                                   f'container is already open. Please close '
                                   f'the container first.')
            if environment is not self:
                environment.open()
                self._container_environment = environment
                self._session_linked = environment._session_linked
            self._container_contexts.append(self)
        else:
            raise RuntimeError(f"Environment {environment} not found. Try "
                               f"opening it if it is a container.")

    def close(self):
        """Close a container.

        No objects can be added to, removed from or fetched from a
        container while it is closed.

        - Raise RuntimeError if self is not on the top of the stack.
        - Changes `_session_linked` to None.
        - Removes self from the top of the stack.
        """
        if self is not self._container_contexts[-1]:
            raise RuntimeError("This is not the least recently opened "
                               "container, cannot close it.")
        self._container_contexts.pop()
        if self not in self._container_contexts:
            self._session_linked = None
            if self._container_environment is not None:
                self._container_environment.close()
                self._container_environment = None

    _container_contexts: List['Container'] = []
    """The context of the most recently opened container."""
    _container_environment: Optional['Container'] = None
    """The container in which this container has been opened (if applies)."""

    def __enter__(self):
        """Sets the container context to this container.

        Essentially just opens self without arguments.
        """
        self.open()
        self._session_linked.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sets the container context to the previous container.

        Essentially just closes self.
        """
        self._session_linked.__exit__()
        self.close()

    # Methods that require the container to be open.
    # --------------------------------------------------------------

    def add(self, *individuals: OntologyIndividual):
        """Adds ontology individuals to a container.

        - Needs the container to be open to operate, tries to open it.
          Closes it after the operation is finished.

        - (Add individual) Adds the individual to
          `session_linked`'s bag if not already there. The
          individual's session may be different from
          `session_linked'. Do the usual stuff in such case
          (put individual in added/updated buffer).

        - (Link individual) Add triples (URIRef(f'<self.iri>'),
          <osp-core:contains>,  URIRef(f'{individual.iri}')) for each
          individual in `individuals` to `self.session`'s graph.

          Such a triple means that the individual is linked to the container.

        - Does NOT add duplicate triples to the container (useless), not
          what users would expect.
        """
        with self:
            for individual in individuals:
                self._session_linked.store(individual)
                self.session.graph.add((self.identifier,
                                        cuba.contains.identifier,
                                        individual.identifier))

    def remove(self, *individuals: OntologyIndividual):
        """Removes ontology individuals from a container.

        - Needs the container to be open to operate, tries to open it. Closes
          it after the operation is finished.

        - Raises ValueError if the individual is not linked to the container.

        - (Remove individual) Removes the individual from
          `session_linked`'s bag.

        - Raises ValueError if the individual is not in
          `session_linked`'s bag.

        - (Unlink individual) Remove all triples with the pattern
          (URIRef(f'<self.iri>'), <osp-core:contains>,
          URIRef(f'{individual.iri}')) from `self.session`'s graph.  This means
          that the individual is no longer linked to the container.
        """
        with self:
            value_errors = set()
            to_remove = set()
            for individual in individuals:
                if individual not in self:
                    value_errors.add(individual)
                else:
                    to_remove.add(individual)

            if value_errors:
                raise ValueError('The following entities cannot be '
                                 'removed, since they are not in '
                                 + f'container {self}: %s' %
                                 ', '.join(f'{individual}' for
                                           individual in value_errors))
            for individual in to_remove:
                self.session.graph.remove((self.identifier,
                                           cuba.contains.identifier,
                                           individual.identifier))

    def __iter__(self) -> Iterator[OntologyIndividual]:
        """Yields ontology individuals from `session_linked`.

        - Needs the container to be open to operate, tries to open it. Closes
          it after the operation is finished.

        - Raise warning when some a linked individual is unreachable in
          `session_linked`.
        """
        with self:
            for reference in self.references:
                try:
                    yield self.session_linked.from_identifier(reference)
                except KeyError:
                    logger.warning(f"Container {self} is connected to "
                                   f"reference {reference}, but such "
                                   f"reference is unavailable in its linked "
                                   f"session {self._session_linked}.")

    def __len__(self) -> int:
        """Returns the number of individuals available to the container.

        - Needs the container to be open to operate, tries to open it. Closes
          it after the operation is finished.

        - Raise warning when some linked individuals are unreachable in
          `session_linked`.
        """
        length = 0
        with self:
            for reference in self.references:
                try:
                    self.session_linked.from_identifier(reference)
                    length += 1
                except KeyError:
                    pass
        return length

    def __contains__(self, entity: OntologyIndividual) -> bool:
        """Checks whether an individual is in the container.

        - Needs the container to be open to operate, tries to open it. Closes
        it after the operation is finished.
        """
        with self:
            if entity.identifier not in self.references:
                return False
            try:
                self.session_linked.from_identifier(entity.identifier)
                return True
            except KeyError:
                return False

    # Methods that do NOT require the container to be open.
    # -------------------------------------------------------------------------
    def connect(self, *references: Iterable[Union[URIRef, str]]):
        """Connects the references to individuals to the container.

        - Does NOT need the container to be open to operate.

        - (Link individual).
        """
        references = set(map(lambda x: URIRef(x), references))
        self.references = set(self.references).union(references)

    def disconnect(self, *references: Union[URIRef, str]):
        """Disconnects the references to individuals from the container.

        - Does NOT need the container to be open to operate.

        - (Unlink individual).
        """
        references = set(map(lambda x: URIRef(x), references))
        self.references = set(self.references).difference(references)
