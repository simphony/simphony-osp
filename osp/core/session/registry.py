# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from uuid import UUID


class Registry(dict):

    def __setitem__(self, key, value):
        message = 'Operation not supported.'
        raise TypeError(message)

    def __getitem__(self, key):
        message = 'Operation not supported.'
        raise TypeError(message)

    def put(self, cuds_object):
        """
        Adds an object to the registry.

        :param cuds_object: The cuds_object to put in the registry
        :type cuds_object: Cuds
        :raises ValueError: unsupported object provided (not a Cuds object)
        """
        from osp.core.cuds import Cuds
        if isinstance(cuds_object, Cuds):
            super().__setitem__(cuds_object.uid, cuds_object)
        else:
            message = '{!r} is not a cuds'
            raise ValueError(message.format(cuds_object))

    def get(self, uid):
        """
        Returns the object corresponding to a given uuid.

        :param uid: uuid of the desired object
        :type uid: UUID
        :return: Cuds object with the uid
        :raises ValueError: unsupported key provided (not a UUID object)
        """
        if isinstance(uid, UUID):
            return super().__getitem__(uid)
        else:
            message = '{!r} is not a proper uuid'
            raise ValueError(message.format(uid))

    def get_subtree(self, root, rel=None, skip=None):
        """Get all the elements in the subtree which is rooted
        in the cuds_object element with the given uid.
        Only consider the given relationship.

        :param root: The root of the subtree.
        :type root: Union[UUID, Cuds]
        :param rel: The relationship to consider defaults to None
        :type rel: Relationship, optional
        :param skip: The elements to skip, defaults to None
        :type skip: Set[Cuds], optional
        :return: The set of elements in the subtree rooted in the given uid.
        :rtype: Set[Cuds]
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
        """Remove all elements in the registry that are reachable from
        the given roots by considering relationship rel.

        :param roots: Remove all elements not reachable from these root
            elements.
        :type root_uids: List[Union[UUID, Cuds]]
        :param rel: Only consider this relationship.
        :type rel: Relationship
        :return: The set of removed elements.
        :rtype: List[Cuds]
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

        # remove the non-reachable ones
        for cuds_object in delete:
            super().__delitem__(cuds_object.uid)
        return delete

    def reset(self):
        """Delete the contents of the registry"""
        keys = set(self.keys())
        for key in keys:
            del self[key]

    def filter(self, criterion):
        """Filter the registry. Return a dictionary that is
        a subset of the registry. It contains only cuds objects
        that satisfy the given criterion.

        :param criterion: A function that decides whether a cuds object
            should be returned. If the function returns True on a cuds object
            it means the cuds object satisfies the criterion.
        :type criterion: Callable[Cuds, bool]
        :return: A dict contains the cuds objects satisfying the criterion.
        :rtype: Dict[UUID, Cuds]
        """
        result = dict()
        for uid, cuds_object in super().items():
            if criterion(cuds_object):
                result[uid] = cuds_object
        return result

    def filter_by_oclass(self, oclass):
        """Filter the registry by ontolgy class.

        :param oclass: The oclass used for filtering.
        :type oclass: OntologyClass
        :return: A subset of the registry,
            containing cuds objects with given ontology class.
        :rtype: Dict[UUID, Cuds]
        """
        return self.filter(lambda x: x.oclass == oclass)

    def filter_by_attribute(self, attribute, value):
        """Filter by attribute and valie

        :param attribute: The attribute to look for
        :type attribute: str
        :param value: The corresponding value to look for
        :type value: Any
        :return: A subset of the registry,
            containing cuds objects with given attribute and value.
        :rtype: Dict[UUID, Cuds]
        """
        return self.filter(lambda x: hasattr(x, attribute)
                           and getattr(x, attribute) == value)

    def filter_by_relationships(self, relationship,
                                consider_subrelationships=False):
        """Filter the registry by relationships:
        Return cuds objects containing the given relationship.

        :param relationship: The relationship to filter by.
        :type relationship: Type[Relationship]
        :param consider_subrelationships: Whether to return cuds objects
            containing subrelationships of the given relationship,
            defaults to False
        :type consider_subrelationships: bool, optional
        :return: A subset of the registry,
            containing cuds objects with given relationship.
        :rtype: Dict[UUID, Cuds]
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
