"""Special kind of ontology individual designed to organize entities."""

import logging
from typing import Dict, Iterable, Iterator, Optional, Tuple, Union
from weakref import ReferenceType, ref

from rdflib import URIRef

from simphony_osp.namespaces import cuba
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.session.session import Environment, Session
from simphony_osp.utils.cuba_namespace import cuba_namespace
from simphony_osp.utils.datatypes import UID, AttributeValue, Triple

logger = logging.getLogger(__name__)


class Container(Environment, OntologyIndividual):
    """Special kind of ontology individual designed to organize entities."""

    rdf_type = cuba_namespace.Container

    def __init__(
        self,
        uid: Optional[UID] = None,
        session: Optional[Session] = None,
        triples: Optional[Iterable[Triple]] = None,
        attributes: Optional[
            Dict[OntologyAttribute, Iterable[AttributeValue]]
        ] = None,
        merge: bool = False,
    ) -> None:
        """Initialize the container."""
        super().__init__(
            uid=uid,
            session=session,
            triples=triples,
            class_=cuba.Container,
            attributes=attributes,
            merge=merge,
        )
        logger.debug("Instantiated container %s" % self)

    @property
    def opens_in(self) -> Optional[Union[Environment, URIRef]]:
        """Returns where the container opens by default.

        Returns the environment in which the container opens by
        default.

        This is NOT the session where the container is stored. The
        ontological data defining the container can be stored in ANY
        session, just like any other ontology individual.
        """
        if isinstance(self._opens_in, ref):
            # Weak reference to environment Python object.
            return self._opens_in()
        else:
            # IRI, try to match to an environment.
            for context in self._stack_default_environment[::-1]:
                if (
                    hasattr(context, "iri")
                    and getattr(context, "iri") == self._opens_in
                ):
                    return context
            else:
                return self._opens_in

    @opens_in.setter
    def opens_in(self, value: Optional[Environment] = None) -> None:
        """Sets where the container opens by default.

        Sets the session or container in which the container opens by
        default.
        """
        if hasattr(value, "iri"):
            self._opens_in = value.iri
        elif isinstance(value, Environment):
            self._opens_in = ref(value)
        elif value is None:
            self._opens_in = value
        else:
            raise TypeError(f"Expected {Environment}, got " f"{type(value)}.")

    _opens_in: Optional[Union[ReferenceType, URIRef]] = None
    """Where the container opens by default.

    Optional[Union[ReferenceType[Environment], URIRef]]
    """

    _container_environment: Optional["Container"] = None
    """The container in which this container has been opened (if applies)."""

    @property
    def session_linked(self) -> Optional[Session]:
        """Returns session that the container uses to fetch items from."""
        return self._session_linked

    _session_linked: Optional[Session] = None
    """The session that the container uses to fetch items from."""

    @property
    def is_open(self) -> bool:
        """Returns the current status of the container."""
        return self._session_linked is not None

    # Methods that do NOT require the container to be open.
    # -------------------------------------------------------------------------

    @property
    def references(self) -> Tuple[URIRef, ...]:
        """Returns a list of the IRIs of all linked individuals.

        - This works without opening the container (checks the linked
          individuals).

        """
        return tuple(
            self._session.graph.objects(self.identifier, cuba.contains.iri)
        )

    @references.setter
    def references(self, value: Iterable[URIRef]):
        """Replace the current linked individuals with the ones received.

        - This works without opening the container.
        """
        provided = set(value)
        existing = set(
            self._session.graph.objects(self.identifier, cuba.contains.iri)
        )
        add = provided - existing
        remove = existing - provided
        for iri in remove:
            self._session.graph.remove(
                (self.identifier, cuba.contains.iri, iri)
            )
        for iri in add:
            self._session.graph.add((self.identifier, cuba.contains.iri, iri))

    @property
    def num_references(self) -> int:
        """Returns the number of connected individuals.

        - Does NOT need the container to be open to operate.
        """
        return len(
            set(
                self._session.graph.objects(self.identifier, cuba.contains.iri)
            )
        )

    def open(self, environment: Optional[Union[Environment]] = None) -> None:
        """Opens the container in `environment`.

        Relevant when an individual needs to be fetched, added
        or removed.

        - PREVENT OPENING CONTAINER IN ITSELF.

        - DO NOT OPEN IF ALREADY OPEN.

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
            # Try to open in current environment
            environment = self._opens_in or self._stack_default_environment[-1]

        if isinstance(environment, ref):
            # Weak reference to environment Python object.
            environment = environment()
        else:
            # IRI, try to match to an environment.
            for context in self._environment_references:
                if (
                    hasattr(context, "iri")
                    and getattr(context, "iri") == self._opens_in
                ):
                    environment = context
                    break

        if isinstance(environment, Session):
            if False:  # (session_closed) TODO: session should report this.
                raise RuntimeError(
                    f"Cannot open container {self} in closed "
                    f"session {environment}."
                )
            if self.is_open and environment is not self._session_linked:
                raise RuntimeError(
                    f"Attempted to open container {self} in "
                    f"session {environment}, but the "
                    f"has been already opened in "
                    f"{self._session_linked}. Please, "
                    f"close the container first."
                )
            self._session_linked = environment
            self._environment_references.add(self)
            self._session_linked.subscribers.add(self)
        elif isinstance(environment, Container):
            if (
                self.is_open
                and self._session_linked is not environment._session_linked
            ):
                raise RuntimeError(
                    f"Attempted to open container {self} in "
                    f"container {environment}, which is "
                    f"linked to session "
                    f"{environment._session_linked} "
                    f"different from "
                    f"{self._session_linked} in which this "
                    f"container is already open. Please close "
                    f"the container first."
                )
            if environment is not self:
                if not environment.is_open:
                    environment.open()
                self._container_environment = environment
                self._session_linked = environment._session_linked
                self._container_environment.subscribers.add(self)
                self._environment_references.add(self)
        else:
            raise RuntimeError(
                f"Environment {environment} not found. Try "
                f"opening it if it is a container."
            )

    def close(self):
        """Close a container.

        No objects can be added to, removed from or fetched from a
        container while it is closed.

        - Raise RuntimeError if self is not on the top of the stack.
        - Changes `_session_linked` to None.
        - Removes self from the top of the stack.
        """
        if self in self._stack_default_environment:
            raise RuntimeError(
                "Cannot close a container that is currently "
                "being used as a context manager."
            )
        super().close()
        environment = self._container_environment or self._session_linked
        if environment is not None:
            environment.subscribers.remove(self)
        self._session_linked = None
        self._container_environment = None

    def __enter__(self):
        """Sets the container context to this container.

        Essentially just opens self without arguments.
        """
        self.open()
        Environment.__enter__(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sets the container context to the previous container.

        Essentially just closes self.
        """
        Environment.__exit__(self, exc_type, exc_val, exc_tb)

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
          <cuba:contains>,  URIRef(f'{individual.iri}')) for each
          individual in `individuals` to `self.session`'s graph.

          Such a triple means that the individual is linked to the container.

        - Does NOT add duplicate triples to the container (useless), not
          what users would expect.
        """
        with self:
            for individual in individuals:
                self._session_linked.update(individual)
                self.session.graph.add(
                    (
                        self.identifier,
                        cuba.contains.identifier,
                        individual.identifier,
                    )
                )

            result = list(
                self._session_linked.from_identifier(i.identifier)
                for i in individuals
            )
        return result[0] if len(individuals) == 1 else list(result)

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
          (URIRef(f'<self.iri>'), <cuba:contains>,
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
                raise ValueError(
                    "The following entities cannot be "
                    "removed, since they are not in "
                    + f"container {self}: %s"
                    % ", ".join(f"{individual}" for individual in value_errors)
                )
            for individual in to_remove:
                self.session.graph.remove(
                    (
                        self.identifier,
                        cuba.contains.identifier,
                        individual.identifier,
                    )
                )

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
                    logger.warning(
                        f"Container {self} is connected to "
                        f"reference {reference}, but such "
                        f"reference is unavailable in its linked "
                        f"session {self._session_linked}."
                    )

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
