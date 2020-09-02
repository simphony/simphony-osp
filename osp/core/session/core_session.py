"""The core session used as default when no backend is connected."""
from .session import Session


class CoreSession(Session):
    """Core default session for all objects."""

    def __str__(self):
        """Convert the core session object to string."""
        return "<CoreSession object>"

    # OVERRIDE
    def _notify_update(self, cuds_object):
        pass

    # OVERRIDE
    def _notify_delete(self, cuds_object):
        pass

    # OVERRIDE
    def _notify_read(self, cuds_object):
        pass

    def _get_full_graph(self):
        """Get the triples in the core session."""
        return self.graph
