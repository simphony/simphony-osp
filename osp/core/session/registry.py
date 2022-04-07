"""The registry stores all local CUDS objects."""

import logging
from uuid import UUID

from rdflib import URIRef

import osp.core.warnings as warning_settings

logger = logging.getLogger(__name__)


class Registry(dict):
    """A dictionary that contains all local CUDS objects."""

    # TODO let the registry act on the graph only.
    # Don't maintain this separate dict.

    def __setitem__(self, key, value):
        """Enforce the use of put()."""
        message = "Operation not supported."
        raise TypeError(message)

    def __getitem__(self, key):
        """Enforce the use of get()."""
        message = "Operation not supported."
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
            message = "{!r} is not a cuds"
            raise ValueError(message.format(cuds_object))

    def get(self, uid):
        """Return the object corresponding to a given uid.

        Args:
            uid (Union[UUID, URIRef]): The uid of the desired
                object.

        Raises:
            ValueError: Unsupported key provided (not a uid object).

        Returns:
            Cuds: Cuds object with the uid.
        """
        if isinstance(uid, (UUID, URIRef)):
            return super().__getitem__(uid)
        else:
            message = "{!r} is not a proper uid"
            raise ValueError(message.format(uid))

    def get_subtree(
        self, root, subtree=None, rel=None, skip=None, warning=None
    ):
        """Get all the elements in the subtree rooted at given root.

        Only use the given relationship for traversal.

        Args:
            root (Union[UUID, URIRef, Cuds]): The root of the subtree.
            rel (Relationship, optional): The relationship used for traversal.
                Defaults to None. Defaults to None.
            subtree (Set[Cuds]): Currently calculated subtree (this is a
                recursive algorithm).
            skip (Set[Cuds], optional): The elements to skip. Defaults to None.
                Defaults to None.
            warning (LargeDatasetWarning, optional): Raise a
                `LargeDatasetWarning` when the subtree is large. When `None`,
                no warning is raised. If you wish to raise the warning, a
                `LargeDatasetWarning` object must be provided.

        Returns:
            Set[Cuds]: The set of elements in the subtree rooted in the given
                uid.
        """
        if isinstance(root, (UUID, URIRef)):
            root = super().__getitem__(root)
        assert root.uid in self
        skip = skip or set() | {root}
        skip |= {root}
        subtree = subtree or {root}

        subclasses = set() if rel is None else rel.subclasses
        subclass_check = (
            (lambda r: True) if not subclasses else (lambda r: r in subclasses)
        )
        """Checks whether relationship `x` should be considered.

        - When no `rel` is provided, `subclass_check` should always return
          True, as all relationships should be considered.

        - When `rel` is provided, it should return true only if the
          relationship `x` is a subclass of the provided relationship (`rel`).
        """

        # Load neighbors connected through the relationship
        filtered_neighbors = (
            neighbor
            for r, dict_target in root._neighbors.items()
            if subclass_check(r)
            for neighbor in dict_target
        )
        filtered_neighbors = set(root.session.load(*filtered_neighbors))

        subtree |= filtered_neighbors

        # Optional: raise a `LargeDatasetWarning` if the subtree is too large.
        if (
            warning is not None
            and len(subtree)
            > warning_settings.unreachable_cuds_objects_large_dataset_size
        ):
            warning.warn()
            warning = None

        for neighbor in filter(lambda x: x not in skip, filtered_neighbors):
            self.get_subtree(
                neighbor, subtree=subtree, rel=rel, skip=skip, warning=warning
            )
        return subtree

    def prune(self, *roots, rel=None):
        """Remove all elements in the registry that are not reachable.

        Args:
            rel (Relationship, optional):Only consider this relationship.
                Defaults to None.

        Returns:
            List[Cuds]: The set of removed elements.
        """
        logger.warning(
            "Registry.prune() is deprecated. " "Use Session.prune() instead."
        )
        not_reachable = self._get_not_reachable(*roots, rel=rel)
        for x in not_reachable:
            super().__delitem__(x.uid)
        return not_reachable

    def _get_not_reachable(
        self, *roots, rel=None, return_reachable=False, warning=None
    ):
        """Get all elements in the registry that are not reachable.

        Use the given rel for traversal.

        Args:
            *roots (Union[UUID, URIRef, Cuds]): Get all elements not reachable
                from these root elements.
            rel (Relationship, optional): Only use this relationship for
                traversal. Defaults to None.
            return_reachable (bool): Returns also the uids of the reachable
                cuds.

        Returns:
            Union[List[Cuds],
                  Tuple[List[Cuds], Set[Union[UUID, URIRef]]]]: Either a
                list of the unreachable CUDS when `return_reachable` is False
                or a tuple whose first element is such list, and second
                element a set with the uids of the reachable cuds.
        """
        # Get all reachable Cuds objects
        reachable = set()
        for root in roots:
            reachable |= self.get_subtree(
                root, rel=rel, skip=reachable, warning=warning
            )
        reachable_uids = set([r.uid for r in reachable])

        # Get all the Cuds objects that are not reachable
        delete = list()
        for uid in self.keys():
            if uid not in reachable_uids:
                delete.append(super().__getitem__(uid))
        return delete if not return_reachable else (delete, reachable_uids)

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
            Dict[Union[UUID, URIRef], Cuds]:  dict contains the cuds objects
                satisfying the criterion.
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
            Dict[Union[UUID, URIRef], Cuds]: A subset of the registry,
                containing cuds objects with given ontology class.
        """
        return self.filter(lambda x: x.oclass == oclass)

    def filter_by_attribute(self, attribute, value):
        """Filter by attribute and value.

        Args:
            attribute (str): The attribute to look for.
            value (Any): The corresponding value to look for.

        Returns:
            Dict[Union[UUID, URIRef], Cuds]: A subset of the registry,
                containing cuds objects with given attribute and value.
        """
        return self.filter(
            lambda x: hasattr(x, attribute) and getattr(x, attribute) == value
        )

    def filter_by_relationships(
        self, relationship, consider_subrelationships=False
    ):
        """Filter the registry by relationships.

        Return cuds objects containing the given relationship.

        Args:
            relationship (OntologyRelationship): The relationship to filter by.
            consider_subrelationships (bool, optional): Whether to return CUDS
                objects containing subrelationships of the given relationship.
                Defaults to False.

        Returns:
            Dict[Union[UUID, URIRef], Cuds]: A subset of the registry,
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
