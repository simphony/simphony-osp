# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from uuid import UUID
from .cuds import Cuds


class Registry(dict):

    def __setitem__(self, key, value):
        message = 'Operation not supported.'
        raise TypeError(message)

    def __getitem__(self, key):
        message = 'Operation not supported.'
        raise TypeError(message)

    def put(self, cuds):
        """
        Adds an object to the registry.

        :param cuds
        :raises ValueError: unsupported object provided (not a Cuds object)
        """
        if isinstance(cuds, Cuds):
            super().__setitem__(cuds.uid, cuds)
        else:
            message = '{!r} is not a cuds object'
            raise ValueError(message.format(cuds))

    def get(self, uid):
        """
        Returns the object corresponding to a given uuid.

        :param uid: uuid of the desired object
        :return: Cuds object with the uid
        :raises ValueError: unsupported key provided (not a UUID object)
        """
        if isinstance(uid, UUID):
            return super().__getitem__(uid)
        else:
            message = '{!r} is not a proper uuid'
            raise ValueError(message.format(uid))

    def get_subtree(self, uid):
        """

        :param uid:
        :return:
        """
        root = super().__getitem__(uid)
        subtree = {root}
        # TODO: Find all (actively related) children
        return subtree

    def prune(self):
        pass
