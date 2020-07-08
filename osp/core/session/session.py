from abc import ABC, abstractmethod
from osp.core.session.registry import Registry
from osp.core.session.result import returns_query_result


class Session(ABC):
    """
    Abstract Base Class for all Sessions.
    Defines the common standard API and sets the registry.
    """

    def __init__(self):
        self._registry = Registry()
        self.root = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

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
        deleted = self._registry.prune(self.root, rel=rel)
        for d in deleted:
            self._notify_delete(d)

    def delete_cuds_object(self, cuds_object):
        """Remove a CUDS object. Will (for now) not delete the cuds objects
        contained.

        Args:
            cuds_object (Cuds): The CUDS object to be deleted
        """
        from osp.core import cuba
        if cuds_object.session != self:
            cuds_object = next(self.load(cuds_object.uid))
        if cuds_object.get():
            cuds_object.remove(rel=cuba.relationship)
        del self._registry[cuds_object.uid]
        self._notify_delete(cuds_object)

    @abstractmethod
    def _notify_delete(self, cuds_object):
        """This method is called if some object from the registry is deleted
        by the prune() method.

        :param cuds_object: The cuds_object that has been deleted
        :type cuds_object: Cuds
        """
        pass

    @abstractmethod
    def _notify_update(self, cuds_object):
        """This method is called if some object has been updated-

        :param cuds_object: The cuds_object that has been updated.
        :type cuds_object: Cuds
        """
        pass

    def sync(self):
        pass

    @abstractmethod
    def _notify_read(self, cuds_object):
        """This method is called when the user accesses the attributes or the
        relationships of the cuds_object cuds_object.

        :param cuds_object: The cuds_object that has been accessed.
        :type cuds_object: Cuds
        """
        pass
