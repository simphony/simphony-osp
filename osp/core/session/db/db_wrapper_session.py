"""An abstract session containing method useful for all database backends."""

from abc import abstractmethod
from osp.core.session.wrapper_session import consumes_buffers, WrapperSession
from osp.core.session.result import returns_query_result
from osp.core.session.buffers import BufferContext, EngineContext


class DbWrapperSession(WrapperSession):
    """Abstract class for a DB Wrapper Session."""

    @consumes_buffers
    def commit(self):
        """Commit the changes in the buffers to the database."""
        self.log_buffer_status(BufferContext.USER)
        self._check_cardinalities()
        self._init_transaction()
        try:
            root_obj = self._registry.get(self.root)
            added, updated, deleted = self._buffers[BufferContext.USER]
            self._apply_added(root_obj, added)
            self._apply_updated(root_obj, updated)
            self._apply_deleted(root_obj, deleted)
            self._reset_buffers(BufferContext.USER)
            self._commit()
        except Exception as e:
            self._rollback_transaction()
            raise e
        self.expire_all()

    @returns_query_result
    def load_by_oclass(self, oclass):
        """Load cuds_object with given OntologyClass.

        Will also return cuds objects of subclasses of oclass.

        Args:
            oclass (OntologyClass): Load cuds objects with this ontology class.

        Yields:
            Cuds: The list of loaded cuds objects
        """
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")
        for subclass in oclass.subclasses:
            yield from self._load_by_oclass(subclass)

    def _store(self, cuds_object):
        """Store and object in the database.

        Args:
            cuds_object (Cuds): The Cuds object to add.
        """
        initialize = self.root is None
        super()._store(cuds_object)

        if initialize:
            with EngineContext(self):
                self._init_transaction()
                try:
                    self._initialize()
                    self._load_first_level()
                    self._commit()
                except Exception as e:
                    self._rollback_transaction()
                    raise type(e)(str(e)) from e

    def _commit(self):
        """Commit to the database."""
        self._engine.commit()

    @abstractmethod
    def _initialize(self):
        """Initialize the database. Create missing tables etc."""

    @abstractmethod
    def _apply_added(self, root_obj, buffer):
        """Add the added cuds_objects to the engine."""

    @abstractmethod
    def _apply_updated(self, root_obj, buffer):
        """Update the updated cuds_objects in the engine."""

    @abstractmethod
    def _apply_deleted(self, root_obj, buffer):
        """Delete the deleted cuds_objects from the engine."""

    @abstractmethod
    def _load_first_level(self):
        """Load the first level of children of the root from the database."""

    @abstractmethod
    def _init_transaction(self):
        """Initialize the transaction."""

    @abstractmethod
    def _rollback_transaction(self):
        """Cancel the transaction."""

    @abstractmethod
    def close(self):
        """Close the connection to the database."""

    @abstractmethod
    def _load_by_oclass(self, oclass):
        """Load the cuds_object with the given ontology class.

        Args:
            oclass (OntologyClass): The OntologyClass of the cuds objects.

        Returns:
            Cuds: The loaded cuds_object.
        """

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
        return username, password

    # OVERRIDE
    def _expire_neighour_diff(self, old_cuds_object, new_cuds_object, uids):
        # do not expire if root is loaded
        x = old_cuds_object or new_cuds_object
        if x and x.uid != self.root:
            super()._expire_neighour_diff(old_cuds_object, new_cuds_object,
                                          uids)
