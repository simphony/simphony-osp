"""The registry stores all local CUDS objects."""

from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class Registry(dict):
    """A dictionary that contains all local CUDS objects."""

    def __setitem__(self, key, value):
        """Enforce the use of put()."""
        message = 'Operation not supported.'
        raise TypeError(message)

    def __getitem__(self, key):
        """Enforce the use of get()."""
        message = 'Operation not supported.'
        raise TypeError(message)

    def put(self, cuds_object):
        """Add an object to the registry.

        Args:
            cuds_object (Cuds):  The cuds_object to put in the registry.

        Raises:
            ValueError: Unsupported object provided (not a Cuds object).
        """
        from osp.core.cuds import Cuds
        if isinstance(cuds_object, Cuds):
            super().__setitem__(cuds_object.uid, cuds_object)
        else:
            message = '{!r} is not a cuds'
            raise ValueError(message.format(cuds_object))

    def get(self, uid):
        """Return the object corresponding to a given uuid.

        Args:
            uid (UUID): The UUID of the desired object.

        Raises:
            ValueError: Unsupported key provided (not a UUID object).

        Returns:
            Cuds: Cuds object with the uid.
        """
        if isinstance(uid, UUID):
            return super().__getitem__(uid)
        else:
            message = '{!r} is not a proper uuid'
            raise ValueError(message.format(uid))

    def get_subtree(self, root, rel=None, skip=None):
        """Get all the elements in the subtree rooted at given root.

        Only use the given relationship for traversal.

        Args:
            root (Union[UUID, Cuds]): The root of the subtree.
            rel (Relationship, optional): The relationship used for traversal.
                Defaults to None. Defaults to None.
            skip (Set[Cuds], optional): The elements to skip. Defaults to None.
                Defaults to None.

        Returns:
            Set[Cuds]: The set of elements in the subtree rooted in the given
                uid.
        """
        from osp.core.cuds import Cuds
        skip = skip or set()
        if not isinstance(root, Cuds):
            root = super().__getitem__(root)
        assert root.uid in self
        subtree = {root}
        for child in root.iter(rel=rel):
            if child not in (skip | subtree):
                subtree |= self.get_subtree(child.uid, rel,
                                            skip=(skip | subtree))
        return subtree

    def prune(self, *roots, rel=None):
        """Remove all elements in the registry that are not reachable.

        Args:
            rel (Relationship, optional):Only consider this relationship.
                Defaults to None.

        Returns:
            List[Cuds]: The set of removed elements.
        """
        logger.warning("Registry.prune() is deprecated. "
                       "Use Session.prune() instead.")
        not_reachable = self._get_not_reachable(*roots, rel=rel)
        for x in not_reachable:
            super().__delitem__(x.uid)
        return not_reachable

    def _get_not_reachable(self, *roots, rel=None):
        """Get all elements in the registry that are not reachable.

        Use the given rel for traversal.

        Args:
            *roots (Union[UUID, Cuds]): Get all elements not reachable from
                these root elements.
            rel (Relationship, optional): Only use this relationship for
                traversal. Defaults to None.

        Returns:
            List[Cuds]: The set of non reachable elements.
        """
        # Get all reachable Cuds objects
        reachable = set()
        for root in roots:
            reachable |= self.get_subtree(root, rel=rel, skip=reachable)
        reachable_uids = set([r.uid for r in reachable])

        # Get all the Cuds objects that are not reachable
        delete = list()
        for uid in self.keys():
            if uid not in reachable_uids:
                delete.append(super().__getitem__(uid))
        return delete

    def reset(self):
        """Delete the contents of the registry."""
        keys = set(self.keys())
        for key in keys:
            del self[key]

    def filter(self, criterion):
        """Filter the registry.

        Return a dictionary that is
        a subset of the registry. It contains only cuds objects
        that satisfy the given criterion.

        Args:
            criterion (Callable[Cuds, bool]): A function that decides whether
                a cuds object should be returned. If the function returns True
                on a cuds object it means the cuds object satisfies the
                criterion.

        Returns:
            Dict[UUID, Cuds]:  dict contains the cuds objects satisfying the
                criterion.
        """
        result = dict()
        for uid, cuds_object in super().items():
            if criterion(cuds_object):
                result[uid] = cuds_object
        return result

    def filter_by_oclass(self, oclass):
        """Filter the registry by ontology class.

        Args:
            oclass (OntologyClass): The oclass used for filtering.

        Returns:
            Dict[UUID, Cuds]: A subset of the registry,
                containing cuds objects with given ontology class.
        """
        return self.filter(lambda x: x.oclass == oclass)

    def filter_by_attribute(self, attribute, value):
        """Filter by attribute and value.

        Args:
            attribute (str): The attribute to look for.
            value (Any): The corresponding value to look for.

        Returns:
            Dict[UUID, Cuds]: A subset of the registry,
                containing cuds objects with given attribute and value.
        """
        return self.filter(lambda x: hasattr(x, attribute)
                           and getattr(x, attribute) == value)

    def filter_by_relationships(self, relationship,
                                consider_subrelationships=False):
        """Filter the registry by relationships.

        Return cuds objects containing the given relationship.

        Args:
            relationship (OntologyRelationship): The relationship to filter by.
            consider_subrelationships (bool, optional): Whether to return CUDS
                objects containing subrelationships of the given relationship.
                Defaults to False.

        Returns:
            Dict[UUID, Cuds]: A subset of the registry,
                containing cuds objects with given relationship.
        """
        if consider_subrelationships:
            def criterion(cuds_object):
                for rel in cuds_object._neighbors.keys():
                    if relationship.is_superclass_of(rel):
                        return True
                return False
        else:
            def criterion(cuds_object):
                return relationship in cuds_object._neighbors

        return self.filter(criterion)
