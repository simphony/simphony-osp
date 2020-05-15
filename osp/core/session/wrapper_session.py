import uuid
import logging
from abc import abstractmethod
from osp.core.session.session import Session
from osp.core.session.result import returns_query_result
from osp.core.utils import destroy_cuds_object, clone_cuds_object, \
    get_neighbor_diff
from osp.core.session.buffers import BufferType, BufferContext, \
    EngineContext

logger = logging.getLogger(__name__)


def consumes_buffers(func):
    def f(session, *args, **kwargs):
        with EngineContext(session):
            func(session, *args, **kwargs)
    f.does_consume_buffers = True
    return f


def check_consumes_buffers(func):
    return hasattr(func, "does_consume_buffers") \
        and func.does_consume_buffers


class WrapperSession(Session):
    """
    Common class for all wrapper sessions.
    Sets the engine and creates the sets with the changed elements
    """

    def __init__(self, engine):
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
        pass

    # OVERRIDE
    @returns_query_result
    def load(self, *uids):
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")

        # refresh expired
        expired = frozenset(set(uids) & self._expired)
        missing_uids = [uid for uid in uids
                        if uid not in self._registry or uid in expired]
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
            if old_cuds_object is not None and new_cuds_object is None:
                destroy_cuds_object(self._registry.get(uid))
            yield new_cuds_object

    def expire(self, *cuds_or_uids):
        """Let cuds_objects expire. Expired objects will be reloaded lazily
        when attributed or relationships are accessed.

        :param cuds_or_uids: The cuds_object or uids to expire
        :type cuds_or_uids: Union[Cuds, UUID]
        :return: The set of uids that became expired
        :rtype: Set[UUID]
        """
        uids = set()
        for c in cuds_or_uids:
            if isinstance(c, uuid.UUID):
                uids.add(c)
            else:
                uids.add(c.uid)
        return self._expire(uids)

    def expire_all(self):
        """Let all cuds_objects of the session expire.
        Expired objects will be reloaded lazily
        when attributed or relationships are accessed.

        :return: The set of uids that became expired
        :rtype: Set[UUID]
        """
        return self._expire(set(self._registry.keys()))

    def refresh(self, *cuds_or_uids):
        """Refresh cuds_objects. Load possibly data of cuds_object
        from the backend.

        :param *cuds_or_uids: The cuds_object or uids to refresh
        :type *cuds_or_uids: Union[Cuds, UUID]
        """
        if not cuds_or_uids:
            return
        logger.debug("Refreshing %s in %s" % (list(cuds_or_uids), self))
        list(self.load(*self.expire(*cuds_or_uids)))

    def get_triples(self):
        """Get the triples in the core session"""
        from osp.core.utils import find_cuds_object
        from osp.core.utils import CUBA
        return [
            triple
            for cuds_object in find_cuds_object(lambda x: True,
                                                self._registry.get(self.root),
                                                CUBA.Relationship,
                                                True)
            for triple in cuds_object.get_triples()
        ]

    def log_buffer_status(self, context):
        """Log the current status of the buffers

        Args:
            context (BufferContext): whether to print user or engine buffers
        """
        added, updated, deleted = self._buffers[context]
        for x in added.values():
            logger.debug("%s has been added to %s", x, self)
        for x in updated.values():
            logger.debug("%s has been updated %s", x, self)
        for x in deleted.values():
            logger.debug("%s has been deleted %s", x, self)
        plural = "%s CUDS objects have been %s %s"
        singular = "%s CUDS object has been %s %s"
        logger.info(singular if len(added) == 1 else plural,
                    len(added), "added to", self)
        logger.info(singular if len(updated) == 1 else plural,
                    len(updated), "updated in", self)
        logger.info(singular if len(deleted) == 1 else plural,
                    len(deleted), "deleted from", self)

    # OVERRIDE
    def _store(self, cuds_object):
        """Store the cuds_objects in the registry and add it to buffers.

        :param cuds_object: The cuds_object to store.
        :type cuds_object: Cuds
        """
        from osp.core import CUBA
        # Check if root is wrapper and wrapper is root
        if cuds_object.is_a(CUBA.WRAPPER) and self.root is not None:
            raise RuntimeError("Only one wrapper is allowed per session")

        if not cuds_object.is_a(CUBA.WRAPPER) and self.root is None:
            raise RuntimeError("Please add a wrapper to the session first")

        # update buffers
        logger.debug("Called store on %s in %s" % (cuds_object, self))
        added, updated, deleted = self._buffers[self._current_context]
        if cuds_object.uid in deleted:
            logger.debug("Removed %s from deleted buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            del deleted[cuds_object.uid]

        if cuds_object.uid in self._registry:
            logger.debug("Added %s to updated buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            updated[cuds_object.uid] = cuds_object
        else:
            logger.debug("Added %s to added buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            added[cuds_object.uid] = cuds_object

        # store
        super()._store(cuds_object)

    # OVERRIDE
    def _notify_update(self, cuds_object):
        """Add the updated cuds_object to the buffers.

        :param cuds_object: The cuds_object that has been updated.
        :type cuds_object: Cuds
        :raises RuntimeError: The updated object has been deleted previously.
        """
        logger.debug("Called notify_update on %s in %s" % (cuds_object, self))
        added, updated, deleted = self._buffers[self._current_context]
        if cuds_object.uid in deleted:
            raise RuntimeError("Cannot update deleted object")

        if cuds_object.uid not in added and cuds_object.uid not in updated:
            logger.debug("Added %s to updated buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            updated[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_delete(self, cuds_object):
        """Add the deleted cuds_object to the buffers.

        :param cuds_object: The cuds_object that has been deleted.
        :type cuds_object: Cuds
        """
        logger.debug("Called notify_delete on %s" % cuds_object)
        added, updated, deleted = self._buffers[self._current_context]
        if cuds_object.uid in added:
            logger.debug("Removed %s from added buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            del added[cuds_object.uid]
        elif cuds_object.uid in updated:
            logger.debug("Moved %s from updated to deleted buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            del updated[cuds_object.uid]
            deleted[cuds_object.uid] = cuds_object
        elif cuds_object.uid not in deleted:
            logger.debug("Added %s to deleted buffer in %s of %s"
                         % (cuds_object, self._current_context, self))
            deleted[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_read(self, cuds_object):
        logger.debug("Called notify_read on %s in %s" % (cuds_object, self))
        if cuds_object.uid in self._expired:
            self.refresh(cuds_object)

    def _expire(self, uids):
        """Expire the given uids

        :param uids: The uids to expire
        :type uids: Set[UUID]
        """
        not_expirable = uids & self._get_buffer_uids(BufferContext.USER)
        logger.debug("Expire %s in %s" % (uids, self))
        if not_expirable:
            logger.warning("Did not expire %s, because you have uncommitted "
                           "local changes. You might be out of sync with "
                           "the backend." % not_expirable)
            uids -= not_expirable
        self._expired |= uids
        self._expired &= self._registry.keys()
        return uids & self._registry.keys()

    def _reset_buffers(self, context):
        """Reset the buffers.

        :param context: Which buffers to reset
        :type context: BufferContext
        :return: Whether the buffers have been resetted.
        :rtype: bool
        """
        logger.debug("Reset buffers for %s in %s" % (context, self))
        self._buffers[context] = [0] * 3
        self._buffers[context][BufferType.ADDED] = dict()
        self._buffers[context][BufferType.UPDATED] = dict()
        self._buffers[context][BufferType.DELETED] = dict()

    def _get_buffer_uids(self, context):
        """Get all the uids of CUDS objects in buffers

        :param context: Which buffers to consider
        :type context: BufferContext
        :return: The uids of cuds objects in buffers
        :rtype: Set[UUID]
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

        :param uids: List of uids to load
        :type uids: List[UUID]
        :param expired: Which of the cuds_objects are expired.
        :type expired: Set[UUID]
        """

    def _get_next_missing(self, missing):
        """Get the next missing cuds object from the iterator.

        :param missing: The iterator over loaded missing cuds objects.
        :type missing: Iterator[Optional[Cuds]]
        :return: The next loaded cuds object or None, if it doesn't exist
        :rtype: Optional[Cuds]
        """
        try:
            cuds_object = next(missing)
        except StopIteration:
            cuds_object = None  # not available in the backend
        return cuds_object

    def _expire_neighour_diff(self, old_cuds_object, new_cuds_object, uids):
        """Expire outdated neighbors of the just loaded cuds object.

        :param old_cuds_object: The old version of the cuds object
        :type old_cuds_object: Optional[Cuds]
        :param new_cuds_object: The just loaded version of the cuds object
        :type new_cuds_object: Optional[Cuds]
        :param uids: The uids that are loaded right now.
        :type uids: List[UUID]
        """
        if old_cuds_object:
            diff1 = get_neighbor_diff(new_cuds_object, old_cuds_object)
            diff1 = set([x[0] for x in diff1])
            diff2 = get_neighbor_diff(old_cuds_object, new_cuds_object)
            diff2 = set([x[0] for x in diff2])
            diff = (diff1 | diff2) - set(uids)
            self._expire(diff)

    def _get_old_cuds_object_clone(self, uid):
        """Get old version of expired cuds object from registry

        :param uid: The uid to get the old cuds object
        :type uid: UUID
        :return: A clone of the old cuds object
        :rtype: Optional[Cuds]
        """
        old_cuds = None
        if uid in self._registry:
            old_cuds = clone_cuds_object(self._registry.get(uid))
        return old_cuds

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
        """Check if the cardinalities specified in the ontology
        are satisfied for the added and updated cuds_object."""
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
    #     from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
    #     ontology_cardinalities, consider_relationships = \
    #         WrapperSession._get_ontology_cardinalities(cuds_object)

    #     # Count the observed cardinalities
    #     observed_cardinalities = {k: 0
    #                               for k in ontology_cardinalities.keys()}
    #     for rel in consider_relationships:
    #         for _, cuba in cuds_object[rel].items():
    #             for r, o in ontology_cardinalities.keys():
    #                 if issubclass(rel, r) \
    #                         and issubclass(CUBA_MAPPING[cuba], o):
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
    #     from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
    #     ontology_cardinalities = dict()
    #     consider_relationships = set()
    #     for rel, objects in cuds_object.supported_relationships.items():
    #         for obj, options in objects.items():
    #             cardinality = Cuds.CUDS_SETTINGS["default_cardinality"]
    #             if options and "cardinality" in options:
    #                 cardinality = options["cardinality"]
    #             cardinality = WrapperSession._parse_cardinality(cardinality)
    #             rel_cls = CUBA_MAPPING[rel]
    #             obj_cls = CUBA_MAPPING[obj]
    #             ontology_cardinalities[rel_cls, obj_cls] = cardinality
    #             consider_relationships |= cuds_object._relationship_tree \
    #                 .get_subrelationships(rel_cls)
    #     return ontology_cardinalities, consider_relationships
