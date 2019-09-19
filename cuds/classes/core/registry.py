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
        from cuds.classes.core.cuds import Cuds
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
        from cuds.classes.core.cuds import Cuds
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
