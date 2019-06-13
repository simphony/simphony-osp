# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid

from ...utils import check_arguments
from ..generated.cuba import CUBA


class DataContainer(dict):
    """
    A DataContainer instance

    The DataContainer object is implemented as a python dictionary whose keys
    are restricted to the instance's `restricted_keys`, default to the CUBA
    enum members.
    """
    DEFAULT_RELATIONSHIP = CUBA.HAS_PART
    DEFAULT_REVERSE = CUBA.IS_PART_OF

    def __init__(self, name):
        """
        Initialization follows the behaviour of the python dict class.
        """
        super().__init__()

        # These are the allowed CUBA keys (faster to convert to set for lookup)
        self.restricted_keys = frozenset(CUBA)

        self.name = name
        self.uid = uuid.uuid4()

    def __setitem__(self, key, value):
        """
        Set/Update the key value only when the key is a CUBA key.

        :param key: key in the dictionary
        :param value: new value to assign to the key
        :raises ValueError: unsupported key provided (not a CUBA key)
        """
        if key in self.restricted_keys:
            super().__setitem__(key, value)
        else:
            message = 'Key {!r} is not in the supported keywords'
            raise ValueError(message.format(key))

    def add(self, *args, rel=None):
        """
        Adds (a) cuds object(s) to their respective CUBA key entries.
        Before adding, check for invalid keys to aviod inconsistencies later.

        :param args: object(s) to add
        :param rel: class of the relationship between the objects
        :return: reference to itself
        :raises ValueError: adding an element already there
        """
        check_arguments('all_simphony_wrappers', *args)
        # TODO: Check the type of the rel object
        relationship = self.DEFAULT_RELATIONSHIP if rel is None else rel.cuba_key

        if relationship not in self.keys():
            self.__setitem__(rel, set())

        for arg in args:
            self._add_direct(arg, relationship)
            arg.add_reverse(self, relationship)
        return self

    def _add_direct(self, entity, rel):
        """
        Adds an entity to the current instance with a specific relationship
        :param entity: object to be added
        :param rel: relationship with the entity to add
        """
        if entity not in self.__getitem__(rel):
            self.__getitem__(rel).add(entity)
        else:
            message = '{!r} is already in the container'
            raise ValueError(message.format(entity))

    def add_reverse(self, entity, rel):
        """
        Adds the reverse relationship to entity.

        :param entity: container of the normal relationship
        :param rel: direct relationship
        """
        reverse_rel = self.DEFAULT_REVERSE if rel is None else rel.reverse
        self._add_direct(entity, reverse_rel)

    def get(self, *uids, rel=None, cuba_key=None):
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(*uids), get(cuba_key), get(*uids, rel)

        :param uids: UIDs of the elements
        :param rel: CUBA key of the relationship
        :param cuba_key: type of the subelements
        :return: list of queried objects, or None, if not found
        """
        output = []
        if rel is None:
            # get by cuba_key
            if not uids:
                check_arguments(CUBA, cuba_key)
                for relationship_set in self.values():
                    for entity in relationship_set:
                        if entity.cuba_key == cuba_key:
                            output.append(entity)
            # get by uids
            if cuba_key is None:
                check_arguments(uuid.UUID, *uids)
                for uid in uids:
                    output.append(self._get_entity_by_uid(uid))
        # get by uids and rel
        elif cuba_key is None:
            check_arguments(uuid.UUID, *uids)
            # TODO: check type of rel
            for uid in uids:
                relationship_set = self.__getitem__(rel.cuba_key)
                output.append(
                    self._get_entity_from_relationship_set(uid,
                                                           relationship_set))
        else:
            message = \
                'Supported calls are get(*uids), get(cuba_key), get(*uids, rel)'
            raise TypeError(message)

        return output

    def _get_entity_by_uid(self, uid):
        """
        Finds an entity in the contained ones by uid.

        :param uid: unique identifier of the wanted entity
        :return: the entity with that uid or None
        """
        for relationship_set in self.values():
            for entity in relationship_set:
                if entity.uid == uid:
                    return entity
        return None

    def _get_entity_from_relationship_set(self, uid, relationship_set):
        """
        Finds an entity under a given relationship set by uid.

        :param uid: unique identifier of the wanted entity
        :param relationship_set:
        :return: the entity with that uid or None
        """
        for entity in relationship_set:
            if entity.uid == uid:
                return entity
        return None

    def remove(self, *args):
        """
        Removes an element from the DataContainer and thus
        also its contained elements.

        :param args: object or UID of the object to remove
        """
        check_arguments((uuid.UUID, DataContainer), *args)
        for arg in args:
            # Erase a UID
            cuba_key = None
            if isinstance(arg, uuid.UUID):
                for cuba_key in self.keys():
                    # UID is a key on that dict
                    if arg in self.__getitem__(cuba_key):
                        del self.__getitem__(cuba_key)[arg]
                        break
            else:
                cuba_key = arg.cuba_key
                del self.__getitem__(cuba_key)[arg.uid]

            # Erase the CUBA key entry if empty
            if not self.__getitem__(cuba_key):
                self.__delitem__(cuba_key)

    def update(self, *args):
        """
        Updates the object with the newer objects.

        :param args: element(s) to update
        :raises ValueError: if an element to update does not exist
        """
        check_arguments('all_simphony_wrappers', *args)
        for arg in args:
            key = arg.cuba_key
            try:
                self.__getitem__(key)[arg.uid] = arg
            except KeyError:
                message = '{} does not exist. Add it first'
                raise ValueError(message.format(arg))

    def iter(self, cuba_key=None):
        """
        Iterates over all the objects contained or over a specific type.

        :param cuba_key: type of the objects to iterate through
        """
        if cuba_key is None:
            yield from self.iter_all()
        else:
            check_arguments(CUBA, cuba_key)
            yield from self.iter_by_key(cuba_key)

    def iter_all(self):
        """
        Iterates over all the first level children
        """
        # Dictionary with entities of the same CUBA key
        for element in self.values():
            for item in element.values():
                yield item

    def iter_by_key(self, cuba_key):
        """
        Iterates over the first level children of a specific type

        :param cuba_key: type of the children to filter
        """
        try:
            yield from self.__getitem__(cuba_key).values()
        # No elements for that key
        except KeyError:
            pass
