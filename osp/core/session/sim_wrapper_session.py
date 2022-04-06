"""Abstract class that contains important method of a simulation session."""

from abc import abstractmethod

from osp.core.session.buffers import BufferContext

from .wrapper_session import WrapperSession, consumes_buffers


class SimWrapperSession(WrapperSession):
    """Abstract class used for simulation sessions.

    Contains methods necessary for all simulation sessions.
    """

    def __init__(self, engine, **kwargs):
        """Initialize the simulation session.

        Args:
            engine (Any): The simulation engine object.
        """
        super().__init__(engine, **kwargs)
        self._ran = False

    @consumes_buffers
    def run(self):
        """Run the simulation."""
        self.log_buffer_status(BufferContext.USER)
        self._check_cardinalities()
        root_obj = self._registry.get(self.root)
        added, updated, deleted = self._buffers[BufferContext.USER]
        if not self._ran:
            self._initialize(root_obj, added)
        else:
            self._apply_added(root_obj, added)
            self._apply_updated(root_obj, updated)
            self._apply_deleted(root_obj, deleted)
        self._reset_buffers(BufferContext.USER)
        self._run(root_obj)
        self._ran = True
        self.expire_all()

    @abstractmethod
    def _run(self, root_cuds_object):
        """Run the engine.

        Args:
            root_cuds_object (Cuds): The wrapper cuds object
        """

    @abstractmethod
    def _apply_added(self, root_obj, buffer):
        """Add the added cuds_objects to the engine.

        Args:
            root_obj (Cuds): The wrapper cuds object
            buffer (Dict[UUID, Cuds]): All Cuds objects that have been added
        """

    @abstractmethod
    def _apply_updated(self, root_obj, buffer):
        """Update the updated cuds_objects in the engine.

        Args:
            root_obj (Cuds): The wrapper cuds object
            buffer (Dict[UUID, Cuds]): All Cuds objects that have been updated
        """

    @abstractmethod
    def _apply_deleted(self, root_obj, buffer):
        """Delete the deleted cuds_objects from the engine.

        Args:
            root_obj (Cuds): The wrapper cuds object.
            buffer (Dict[UUID, Cuds]): All Cuds objects that have been deleted
        """

    def _initialize(self, root_obj, buffer):
        """Initialize the session.

        This method is executed before the first run.

        Args:
            root_obj (Cuds): The wrapper cuds object.
            buffer (Dict[UUID, Cuds]): All Cuds objects that have been added
        """
        self._apply_added(root_obj, buffer)
