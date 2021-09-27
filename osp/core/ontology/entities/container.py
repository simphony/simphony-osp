"""Special kind of ontology individual designed to organize entities."""

from rdflib import URIRef

from typing import (Iterable, Iterator, List, Optional, TYPE_CHECKING,
                    Tuple, Union)

if TYPE_CHECKING:
    from osp.core.session.session import Session

from osp.core.ontology.individual import OntologyIndividual


class Container(OntologyIndividual):
    """Special kind of ontology individual designed to organize entities."""

    _container_contexts: List[Union['Container', Session]] = []
    """The context of the most recently opened container."""

    @property
    def opens_in(self) -> Optional[Union['Container', Session]]:
        """Returns where the container opens by default.

        Returns the session or container in which the container opens by
        default.

        This is NOT the session where the container is stored. The
        ontological data defining the container can be stored in ANY
        session, just like any other ontology individual.
        """
        pass

    @opens_in.setter
    def opens_in(self,
                 value: Optional[Union['Container', Session]] = None) -> None:
        """Sets where the container opens by default.

        Sets the session or container in which the container opens by
        default.
        """
        self._opens_in = value

    _opens_in: Optional[Union['Container', Session]] = None
    """Where the container opens by default."""

    @property
    def session_linked(self) -> Optional['Session']:
        """Returns session that the container uses to fetch items from."""
        return self._session_linked

    _session_linked: Optional['Session'] = None
    """The session that the container uses to fetch items from."""

    @property
    def is_open(self) -> bool:
        """Returns the current status of the container.

        - Derived from the `_container_contexts` stack. If the container is
          there, then it is open.
        """
        pass

    # Methods that do NOT require the container to be open.
    # -------------------------------------------------------------------------

    @property
    def references(self) -> Tuple[URIRef, ...]:
        """Returns a list of the IRIs of all linked individuals.

        - This works without opening the container (checks the linked
          individuals).

        """
        pass

    @references.setter
    def references(self, value: Iterable[URIRef]):
        """Replace the current linked individuals by the ones received.

        - This works without opening the container.
        """
        pass

    @property
    def num_references(self) -> int:
        """Returns the number of connected individuals.

        - Does NOT need the container to be open to operate.
        """
        pass

    def open(self,
             environment: Optional[Union['Session',
                                         'Container']] = None) -> None:
        """Opens the container in `environment`.

        Relevant when an individual needs to be fetched, added
        or removed.

        - PREVENT OPENING CONTAINER IN ITSELF.

        - DO NOT OPEN IF ALREADY OPEN.

        # Issue: session and container stacks need to be mixed somehow
        # (handled later).

        - If no environment (session or container) is provided:
            - Try to open in `open_in` if not None.
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
        pass

    def close(self):
        """Close a container.

        No objects can be added to, removed from or fetched from a
        container while it is closed.

        - Raise RuntimeError if self is not on the top of the stack.
        - Changes `_session_linked` to None.
        - Removes self from the top of the stack.
        """
        pass

    def __enter__(self):
        """Sets the container context to this container.

        Essentially just opens self without arguments.
        """
        return self

    def __exit__(self):
        """Sets the container context to the previous container.

        Essentially just closes self.
        """
        pass

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
        pass

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
        pass

    def __iter__(self) -> Iterator[OntologyIndividual]:
        """Yields ontology individuals from `session_linked`.

        - Needs the container to be open to operate, tries to open it. Closes
          it after the operation is finished.

        - Raise warning when some a linked individual is unreachable in
          `session_linked`.
        """
        pass

    def __len__(self) -> int:
        """Returns the number of individuals available to the container.

        - Needs the container to be open to operate, tries to open it. Closes
          it after the operation is finished.

        - Raise warning when some linked individuals are unreachable in
          `session_linked`.
        """
        pass

    def __contains__(self, entity: OntologyIndividual):
        """Checks whether an individual is in the container.

        - Needs the container to be open to operate, tries to open it. Closes
        it after the operation is finished.
        """
        pass

    # Methods that do NOT require the container to be open.
    # -------------------------------------------------------------------------
    def connect(self, *references: Union[URIRef, str]):
        """Connects the references to individuals to the container.

        - Does NOT need the container to be open to operate.

        - (Link individual).
        """
        pass

    def disconnect(self, *references: Union[URIRef, str]):
        """Disconnects the references to individuals from the container.

        - Does NOT need the container to be open to operate.

        - (Unlink individual).
        """
        pass
