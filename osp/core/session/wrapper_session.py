"""Abstract class that contains important method of a session with backend."""

import logging
import uuid
from abc import abstractmethod

import rdflib

from osp.core.namespaces import cuba
from osp.core.session.buffers import BufferContext, BufferType, EngineContext
from osp.core.session.result import returns_query_result
from osp.core.session.session import Session
from osp.core.utils.wrapper_development import (
    clone_cuds_object,
    get_neighbor_diff,
)

logger = logging.getLogger(__name__)


def consumes_buffers(func):
    """Indicate that a session method consumes the buffers.

    Should be used as a decorator.

    Args:
        func (Callable): The method to decorate.
    """

    def f(session, *args, **kwargs):
        with EngineContext(session):
            func(session, *args, **kwargs)

    f.does_consume_buffers = True
    return f


def check_consumes_buffers(func):
    """Check whether a session method consumes the buffers or not.

    Args:
        func (Callable): The method to check

    Returns:
        bool: Whether the given method does consume the buffers.
    """
    return hasattr(func, "does_consume_buffers") and func.does_consume_buffers


class WrapperSession(Session):
    """Common class for all wrapper sessions.

    Sets the engine and creates the sets with the changed elements
    """

    def __init__(self, engine):
        """Initialize the session.

        Args:
            engine (Any): The object that connects to the backend.
        """
        super().__init__()
        self._engine = engine
        self._current_context = BufferContext.USER
        self._buffers = [0] * 2
        self._reset_buffers(BufferContext.USER)
        self._reset_buffers(BufferContext.ENGINE)
        self._expired = set()
        self._remote = False

    @abstractmethod
    def __str__(self):
        """Convert the session to string."""

    # OVERRIDE
    @returns_query_result
    def load(self, *uids):
        """Load the CUDS object with the given uuid from the session.

        If the object either does not exist on the Client side or is expired,
        try to load it from the backend.

        Raises:
            RuntimeError: The Session is not yet initialized.
                Add a Wrapper first.

        Yields:
            Cuds: The CUDS objects with the given UUID.
        """
        if self.root is None:
            raise RuntimeError(
                "This Session is not yet initialized. "
                "Add it to a wrapper first."
            )

        # refresh expired
        expired = frozenset(set(uids) & self._expired)
        missing_uids = [
            uid for uid in uids if uid not in self._registry or uid in expired
        ]
        self._expired -= expired

        # Load elements not in the registry / expired from the backend
        missing = self._load_from_backend(missing_uids, expired=expired)
        for uid in uids:

            # Load from registry if uid is there and not expired
            if uid not in missing_uids:
                yield self._registry.get(uid)
                continue

            # Load from the backend
            old_cuds_object = self._get_old_cuds_object_clone(uid)
            new_cuds_object = self._get_next_missing(missing)
            self._expire_neighour_diff(old_cuds_object, new_cuds_object, uids)
            if (
                old_cuds_object is not None
                and new_cuds_object is None
                and uid in self._registry
            ):
                self._delete_cuds_triples(self._registry.get(uid))
            yield new_cuds_object

    def expire(self, *cuds_or_uids):
        """Let cuds_objects expire.

        Expired objects will be reloaded lazily
        when attributed or relationships are accessed.

        Args:
            *cuds_or_uids (Union[Cuds, UUID, URIRef]): The cuds_object
            or uids to expire.

        Returns:
            Set[UUID]: The set of uids that became expired
        """
        uids = set()
        for c in cuds_or_uids:
            if isinstance(c, (uuid.UUID, rdflib.URIRef)):
                uids.add(c)
            else:
                uids.add(c.uid)
        return self._expire(uids)

    def expire_all(self):
        """Let all cuds_objects of the session expire.

        Expired objects will be reloaded lazily
        when attributed or relationships are accessed.

        Returns:
            Set[UUID]: The set of uids that became expired
        """
        return self._expire(set(self._registry.keys()))

    def refresh(self, *cuds_or_uids):
        """Refresh cuds_objects.

        Load possibly updated data of cuds_object from the backend.

        Args:
            *cuds_or_uids (Union[Cuds, UUID]): The cuds_object or uids to
                refresh.
        """
        if not cuds_or_uids:
            return
        if logger.level == logging.DEBUG:
            logger.debug("Refreshing %s in %s" % (list(cuds_or_uids), self))
        list(self.load(*self.expire(*cuds_or_uids)))

    def _get_full_graph(self):
        """Get the triples in the core session."""
        from osp.core.utils.simple_search import find_cuds_object

        for cuds_object in find_cuds_object(
            lambda x: True,
            self._registry.get(self.root),
            cuba.relationship,
            True,
        ):
            pass
        return self.graph

    def log_buffer_status(self, context):
        """Log the current status of the buffers.

        Args:
            context (BufferContext): whether to print user or engine buffers
        """
        added, updated, deleted = self._buffers[context]
        if logger.level == logging.DEBUG:
            for x in added.values():
                logger.debug("%s has been added to %s", x, self)
            for x in updated.values():
                logger.debug("%s has been updated %s", x, self)
            for x in deleted.values():
                logger.debug("%s has been deleted %s", x, self)
        plural = "%s CUDS objects have been %s %s"
        singular = "%s CUDS object has been %s %s"
        logger.info(
            singular if len(added) == 1 else plural,
            len(added),
            "added to",
            self,
        )
        logger.info(
            singular if len(updated) == 1 else plural,
            len(updated),
            "updated in",
            self,
        )
        logger.info(
            singular if len(deleted) == 1 else plural,
            len(deleted),
            "deleted from",
            self,
        )

    def _store_checks(self, cuds_object):
        # Check if root is wrapper and wrapper is root
        if (
            cuds_object.is_a(cuba.Wrapper)
            and self.root is not None
            and self.root != cuds_object.uid
        ):
            raise RuntimeError("Only one wrapper is allowed per session")

        if not cuds_object.is_a(cuba.Wrapper) and self.root is None:
            raise RuntimeError("Please add a wrapper to the session first")

        if cuds_object.oclass is None:
            if any(
                self.graph.triples((cuds_object.iri, rdflib.RDF.type, None))
            ):
                raise TypeError(
                    f"No oclass associated with {cuds_object}! "
                    f"However, the cuds is supposed to be of "
                    "type(s): %s. Did you install the required "
                    "ontology?"
                    % ", ".join(
                        o
                        for o in self.graph.objects(
                            cuds_object.iri, rdflib.RDF.type
                        )
                    )
                )
            else:
                raise TypeError(
                    f"No oclass associated with {cuds_object}!"
                    f"Did you install the required ontology?"
                )

    # OVERRIDE
    def _store(self, cuds_object):
        """Store the cuds_objects in the registry and add it to buffers.

        Args:
            cuds_object (Cuds): The cuds_object to store.
        """
        if cuds_object.oclass:
            self._store_checks(cuds_object)

        # update buffers
        if logger.level == logging.DEBUG:
            logger.debug("Called store on %s in %s" % (cuds_object, self))
        added, updated, deleted = self._buffers[self._current_context]
        if cuds_object.uid in deleted:
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Removed %s from deleted buffer in %s of %s"
                    % (cuds_object, self._current_context, self)
                )
            del deleted[cuds_object.uid]

        if cuds_object.uid in self._registry:
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Added %s to updated buffer in %s of %s"
                    % (cuds_object, self._current_context, self)
                )
            updated[cuds_object.uid] = cuds_object
        elif not cuds_object.is_a(cuba.Wrapper):
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Added %s to added buffer in %s of %s"
                    % (cuds_object, self._current_context, self)
                )
            added[cuds_object.uid] = cuds_object
        # store
        super()._store(cuds_object)

    # OVERRIDE
    def _notify_update(self, cuds_object):
        """Add the updated cuds_object to the buffers.

        Args:
            cuds_object (Cuds): The cuds_object that has been updated.

        Raises:
            RuntimeError: The updated object has been deleted previously.
        """
        if logger.level == logging.DEBUG:
            logger.debug(
                "Called notify_update on %s in %s" % (cuds_object, self)
            )
        added, updated, deleted = self._buffers[self._current_context]
        if cuds_object.uid in deleted:
            raise RuntimeError("Cannot update deleted object")

        if cuds_object.uid not in added and cuds_object.uid not in updated:
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Added %s to updated buffer in %s of %s"
                    % (cuds_object, self._current_context, self)
                )
            updated[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_delete(self, cuds_object):
        """Add the deleted cuds_object to the buffers.

        Args:
            cuds_object (Cuds): The cuds_object that has been deleted.
        """
        if logger.level == logging.DEBUG:
            logger.debug("Called notify_delete on %s" % cuds_object)
        added, updated, deleted = self._buffers[self._current_context]
        if cuds_object.uid in added:
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Removed %s from added buffer in %s of %s"
                    % (cuds_object, self._current_context, self)
                )
            del added[cuds_object.uid]
        elif cuds_object.uid in updated:
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Moved %s from updated to deleted buffer in %s "
                    "of %s" % (cuds_object, self._current_context, self)
                )
            del updated[cuds_object.uid]
            deleted[cuds_object.uid] = cuds_object
        elif cuds_object.uid not in deleted:
            if logger.level == logging.DEBUG:
                logger.debug(
                    "Added %s to deleted buffer in %s of %s"
                    % (cuds_object, self._current_context, self)
                )
            deleted[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_read(self, cuds_object):
        if logger.level == logging.DEBUG:
            logger.debug(
                "Called notify_read on %s in %s" % (cuds_object, self)
            )
        if cuds_object.uid in self._expired:
            self.refresh(cuds_object)
        if cuds_object.uid not in self._registry and cuds_object._stored:
            cuds_object._graph = rdflib.Graph()

    def _expire(self, uids):
        """Expire the given uids.

        Args:
            uids(Set[UUID]): The uids to expire.
        """
        not_expirable = uids & self._get_buffer_uids(BufferContext.USER)
        logger.debug("Expire %s in %s" % (uids, self))
        if not_expirable:
            logger.warning(
                "Did not expire %s, because you have uncommitted "
                "local changes. You might be out of sync with "
                "the backend." % not_expirable
            )
            uids -= not_expirable
        self._expired |= uids
        self._expired &= self._registry.keys()
        return uids & self._registry.keys()

    def _reset_buffers(self, context):
        """Reset the buffers.

        Args:
            context (BufferContext): Which buffers to reset

        Returns:
            bool: Whether the buffers have been resetted.
        """
        logger.debug("Reset buffers for %s in %s" % (context, self))
        self._buffers[context] = [0] * 3
        self._buffers[context][BufferType.ADDED] = dict()
        self._buffers[context][BufferType.UPDATED] = dict()
        self._buffers[context][BufferType.DELETED] = dict()
        # TODO only buffers for added and deleted triples.

    def _get_buffer_uids(self, context):
        """Get all the uids of CUDS objects in buffers.

        Args:
            context (BufferContext): Which buffers to consider.

        Return:
            Set[Union[UUID, URIRef]]: The uids of cuds objects in
                                      buffers.
        """
        return (
            set(self._buffers[context][BufferType.ADDED].keys())
            | set(self._buffers[context][BufferType.UPDATED].keys())
            | set(self._buffers[context][BufferType.DELETED].keys())
        )

    @abstractmethod
    def _load_from_backend(self, uids, expired=None):
        """Load cuds_object with given uids from the database.

        Will update objects with same uid in the registry.

        Args:
            uids (List[Union[UUID, URIRef]]): List of uids to
                                                     load.
            expired (Set[Union[UUID, URIRef]]): Which of the cuds_objects are
                                                expired.
        """

    def _get_next_missing(self, missing):
        """Get the next missing cuds object from the iterator.

        Args:
            missing (Iterator[Cuds], optional): The iterator over loaded
                missing cuds objects.

        Return:
            Cuds, optional: The next loaded cuds object or None, if it doesn't
                exist.
        """
        try:
            cuds_object = next(missing)
        except StopIteration:
            cuds_object = None  # not available in the backend
        return cuds_object

    def _expire_neighour_diff(self, old_cuds_object, new_cuds_object, uids):
        """Expire outdated neighbors of the just loaded cuds object.

        Args:
            old_cuds_object (Cuds, optional): The old version of the cuds
                object.
            new_cuds_object (Cuds, optional): The just loaded version of the
                cuds object.
            uids (List[Union[UUID, uids]]): The uids that
            are loaded right now.
        """
        if old_cuds_object:
            diff1 = get_neighbor_diff(new_cuds_object, old_cuds_object)
            diff1 = set([x[0] for x in diff1])
            diff2 = get_neighbor_diff(old_cuds_object, new_cuds_object)
            diff2 = set([x[0] for x in diff2])
            diff = (diff1 | diff2) - set(uids)
            self._expire(diff)

    def _get_old_cuds_object_clone(self, uid):
        """Get old version of expired cuds object from registry.

        Args:
            uid (Union[UUID, URIRef]): The uid to get the old
            cuds object.

        Returns:
            Cuds, optional: A clone of the old cuds object
        """
        clone = None
        if uid in self._registry:
            clone = clone_cuds_object(self._registry.get(uid))
        return clone

    @staticmethod
    def handshake(username, connection_id):
        """Will be called on the server, before anything else.

        Result of this method will be fed into compute_auth() below,
        that will be executed by the client.

        Args:
            username (str): The username of the user, as encoded in the URL.
            connection_id (UUID): A UUID for the connection.

        Returns:
            Any: Any JSON serializable object that should be fed into
                compute_auth().
        """
        pass

    @staticmethod
    def compute_auth(username, password, handshake):
        """Will be called on the client, after the handshake.

        This method should produce an object that is able to authenticate
        the user.
        The __init__() method of the session should have a keyword "auth",
        that will have the output of this function as a value.
        --> The user can be authenticated on __init__()

        Args:
            username (str): The username as encoded in the URI.
            password (str): The password as encoded in the URI.
            handshake (Any): The result of the hanshake method.

        Returns:
            Any: Any JSON serializable object that is able to authenticate
            the user.
        """
        pass

    def _check_cardinalities(self):
        """Check if the cardinalities are satisfied.

        The cardinalities are specified in the ontology and the checks are
        performed on the added and updated CUDS objects.
        """
        if self.root is None:
            raise RuntimeError(
                "No wrapper defined for that session. Please instantiate a "
                "wrapper and provide this session as an argument."
            )
        # TODO

    # @staticmethod
    # def _check_cuds_object_cardinalities(cuds_object):
    #     """Check the cardinality of a single cuds_object.

    #     :param cuds_object: The cuds_object to check-
    #     :type cuds_object: Cuds
    #     :raises ValueError: The cuds_object did not satisfy the cardinalities
    #         given by the ontology
    #     """
    #     from cuds.classes.generated.cuba_mapping import cuba_MAPPING
    #     ontology_cardinalities, consider_relationships = \
    #         WrapperSession._get_ontology_cardinalities(cuds_object)

    #     # Count the observed cardinalities
    #     observed_cardinalities = {k: 0
    #                               for k in ontology_cardinalities.keys()}
    #     for rel in consider_relationships:
    #         for _, cuba in cuds_object[rel].items():
    #             for r, o in ontology_cardinalities.keys():
    #                 if issubclass(rel, r) \
    #                         and issubclass(cuba_MAPPING[cuba], o):
    #                     observed_cardinalities[r, o] += 1

    #     # Check if observed cardinalities are consistent
    #     for r, o in ontology_cardinalities.keys():
    #         if not (ontology_cardinalities[r, o][0]
    #                 <= observed_cardinalities[r, o]
    #                 <= ontology_cardinalities[r, o][1]):
    #             raise ValueError(
    #                 ("The number of %s connected to %s via %s"
    #                     + " should be in range %s, but %s given.")
    #                 % (o, cuds_object, r,
    #                     list(ontology_cardinalities[r, o]),
    #                     observed_cardinalities[r, o]))

    # @staticmethod
    # def _parse_cardinality(cardinality):
    #     """Parse the cardinality string given in the ontology:
    #     Allowed: many = * = 0+ / + = 1+ / a+ / a-b / a

    #     :param cardinality: The given cardinality string to parse
    #     :type cardinality: str
    #     :return: A tuple defining the min and max number of occurences
    #     :rtype: Tuple[int, int]
    #     """
    #     min_occurrences = 0
    #     max_occurrences = float("inf")
    #     if isinstance(cardinality, int):
    #         min_occurrences = max_occurrences = cardinality
    #     elif cardinality in ["*", "many"]:
    #         pass
    #     elif cardinality in ["+", "some"]:
    #         min_occurrences = 1
    #     elif cardinality == "?":
    #         min_occurrences = 0
    #         max_occurrences = 1
    #     elif cardinality.endswith("+"):
    #         min_occurrences = int(cardinality[:-1].strip())
    #     elif "-" in cardinality:
    #         min_occurrences = int(cardinality.split("-")[0].strip())
    #         max_occurrences = int(cardinality.split("-")[1].strip())
    #     else:
    #         min_occurrences = max_occurrences = int(cardinality.strip())
    #     return min_occurrences, max_occurrences

    # @staticmethod
    # def _get_ontology_cardinalities(cuds_object):
    #     """Read the cardinalites for the given cuds_object
    #         as specified in the ontology.

    #     :param cuds_object: The given Cuds object.
    #     :type cuds_object: Cuds
    #     :return: Dictionary mapping relationship-Cuds_class
    #         to min and max number of occurences + set of relationships
    #         to consider when checking if cardinalities are satisfied.
    #     :rtype: Tuple[Dict[Tuple[Class, Class], Tuple[int, int]], Set]
    #     """
    #     from cuds.classes.generated.cuba_mapping import cuba_MAPPING
    #     ontology_cardinalities = dict()
    #     consider_relationships = set()
    #     for rel, objects in cuds_object.supported_relationships.items():
    #         for obj, options in objects.items():
    #             cardinality = Cuds.CUDS_SETTINGS["default_cardinality"]
    #             if options and "cardinality" in options:
    #                 cardinality = options["cardinality"]
    #             cardinality = WrapperSession._parse_cardinality(cardinality)
    #             rel_cls = cuba_MAPPING[rel]
    #             obj_cls = cuba_MAPPING[obj]
    #             ontology_cardinalities[rel_cls, obj_cls] = cardinality
    #             consider_relationships |= cuds_object._relationship_tree \
    #                 .get_subrelationships(rel_cls)
    #     return ontology_cardinalities, consider_relationships
