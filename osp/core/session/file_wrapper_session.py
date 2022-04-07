"""Abstract class for a File Wrapper Session."""

from abc import abstractmethod

from osp.core.session.buffers import BufferContext, EngineContext
from osp.core.session.result import returns_query_result
from osp.core.session.wrapper_session import WrapperSession, consumes_buffers


class FileWrapperSession(WrapperSession):
    """Abstract class for a File Wrapper Session.

    A file wrapper session is a session that communicates with the backend
    via files.
    """

    @consumes_buffers
    def save(self):
        """Save the changes in the buffers to the file."""
        self.log_buffer_status(BufferContext.USER)
        self._check_cardinalities()
        self._open()
        root_obj = self._registry.get(self.root)
        added, updated, deleted = self._buffers[BufferContext.USER]
        self._apply_added(root_obj, added)
        self._apply_updated(root_obj, updated)
        self._apply_deleted(root_obj, deleted)
        self._save()
        self._close()
        self._reset_buffers(BufferContext.USER)
        self.expire_all()

    @returns_query_result
    def load_by_oclass(self, oclass):
        """Load cuds_object with given ontology class.

        Will also return cuds objects of subclasses of oclass.

        Args:
            oclass (OntologyClass): The ontology class to query for.

        Raises:
            RuntimeError: Session not yet initialized.

        Yields:
            Cuds: The loaded CUDS objects.
        """
        if self.root is None:
            raise RuntimeError(
                "This Session is not yet initialized. "
                "Add it to a wrapper first."
            )
        for subclass in oclass.subclasses:
            yield from self._load_by_oclass(subclass)

    def _store(self, cuds_object):
        initialize = self.root is None
        super()._store(cuds_object)

        if initialize:
            with EngineContext(self):
                self._initialize()
                self._load_first_level()

    @abstractmethod
    def _open(self):
        """Open the connection to the file."""

    @abstractmethod
    def _close(self):
        """Close the connection to the file."""

    @abstractmethod
    def _apply_added(self, root_obj, buffer):
        """Add the added cuds_objects to the file."""

    @abstractmethod
    def _apply_updated(self, root_obj, buffer):
        """Update the updated cuds_objects in the file."""

    @abstractmethod
    def _apply_deleted(self, root_obj, buffer):
        """Delete the deleted cuds_objects from the file."""

    @abstractmethod
    def _save(self):
        """Save changes to the file."""

    @abstractmethod
    def _initialize(self):
        """Initialize the file. Creates the necessary structures."""

    @abstractmethod
    def _load_first_level(self):
        """Load the first level of children of the root from the database."""

    @abstractmethod
    def _load_by_oclass(self, oclass):
        """Load the cuds_object with the given ontology class.

        Args:
            oclass (OntologyClass): Load cuds objects with given ontology
                class.

        Returns:
            Cuds: The loaded Cuds objects.
        """
