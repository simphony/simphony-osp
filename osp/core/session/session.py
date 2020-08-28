"""Abstract Base Class for all Sessions."""

import rdflib
from abc import ABC, abstractmethod
from osp.core.session.registry import Registry
from osp.core.session.result import returns_query_result


class Session(ABC):
    """Abstract Base Class for all Sessions.

    Defines the common standard API and sets the registry.
    """

    def __init__(self):
        """Initialize the session."""
        self._registry = Registry()
        self.root = None
        self.graph = rdflib.Graph()

    def __enter__(self):
        """Establish the connection to the backend."""
        return self

    def __exit__(self, *args):
        """Close the connection to the backend."""
        self.close()

    def close(self):
        """Close the connection to the backend."""

    @abstractmethod
    def __str__(self):
        """Convert the session to string."""

    def _store(self, cuds_object):
        """Store a copy of given cuds_object in the session.

        Return the stored object.

        :param cuds_object: The cuds_object to store.
        :type cuds_object: Cuds
        :return: The stored cuds_object.
        :rtype: Cuds
        """
        assert cuds_object.session == self
        self._registry.put(cuds_object)
        self.graph |= cuds_object._graph
        cuds_object._graph = self.graph
        if self.root is None:
            self.root = cuds_object.uid

    @returns_query_result
    def load(self, *uids):
        """Load the cuds_objects of the given uids.

        :param uids: The uids of the cuds_objects to load.
        :type uids: UUID
        :return: The fetched Cuds objects.
        :rtype: Iterator[Cuds]
        """
        for uid in uids:
            try:
                yield self._registry.get(uid)
            except KeyError:
                yield None

    def prune(self, rel=None):
        """Remove all elements not reachable from the sessions root.

        Only consider given relationship and its subclasses.

        :param rel: Only consider this relationship to calculate reachability.
        :type rel: Relationship
        """
        deleted = self._registry._get_not_reachable(self.root, rel=rel)
        for d in deleted:
            self._delete_cuds_triples(d)

    def delete_cuds_object(self, cuds_object):
        """Remove a CUDS object.

        Will not delete the cuds objects contained.

        Args:
            cuds_object (Cuds): The CUDS object to be deleted
        """
        from osp.core.namespaces import cuba
        if cuds_object.session != self:
            cuds_object = next(self.load(cuds_object.uid))
        if cuds_object.get(rel=cuba.relationship):
            cuds_object.remove(rel=cuba.relationship)
        self._delete_cuds_triples(cuds_object)

    def _delete_cuds_triples(self, cuds_object):
        """Delete the triples of a given cuds object from the session's graph.

        Args:
            cuds_object (Cuds): The object to delete.
        """
        del self._registry[cuds_object.uid]
        t = self.graph.value(cuds_object.iri, rdflib.RDF.type)
        self.graph.remove((cuds_object.iri, None, None))
        cuds_object._graph = rdflib.Graph()
        cuds_object._graph.set((cuds_object.iri, rdflib.RDF.type, t))
        self._notify_delete(cuds_object)

    @abstractmethod
    def _notify_delete(self, cuds_object):
        """Notify the session that some object has been delted.

        :param cuds_object: The cuds_object that has been deleted
        :type cuds_object: Cuds
        """
        pass

    @abstractmethod
    def _notify_update(self, cuds_object):
        """Notify the session that some object has been updated.

        :param cuds_object: The cuds_object that has been updated.
        :type cuds_object: Cuds
        """
        pass

    def sync(self):
        """Synchronize sessions."""
        pass  # TODO

    @abstractmethod
    def _notify_read(self, cuds_object):
        """Notify the session that given cuds object has been read.

        This method is called when the user accesses the attributes or the
        relationships of the cuds_object cuds_object.

        :param cuds_object: The cuds_object that has been accessed.
        :type cuds_object: Cuds
        """
        pass
