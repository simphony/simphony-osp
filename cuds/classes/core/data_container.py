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
    DEFAULT_DIRECT_REL = CUBA.HAS_PART
    DEFAULT_INVERSE_REL = CUBA.IS_PART_OF

    def __init__(self):
        """
        Initialization follows the behaviour of the python dict class.
        """
        super().__init__()

        # These are the allowed CUBA keys (faster to convert to set for lookup)
        self.restricted_keys = frozenset(CUBA)
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

    def __hash__(self):
        """
        Makes DataContainer objects hashable.
        Use the hash of the uid of the object

        :return: unique hash
        """
        return hash(self.uid)

    def __eq__(self, other):
        """
        Defines the equals.
        Two instances are the same if they share the uid and the class

        :param other: Instance to check
        :return: True if they share the uid and class, false otherwise
        """
        if isinstance(other, self.__class__):
            return self.uid == other.uid
        return False

    def add(self, *args, rel=None):
        """
        Adds (a) cuds object(s) to their respective CUBA key relationship.
        Before adding, check for invalid keys to avoid inconsistencies later.

        :param args: object(s) to add
        :param rel: class of the relationship between the objects
        :return: reference to itself
        :raises ValueError: adding an element already there
        """
        check_arguments('all_simphony_wrappers', *args)
        # TODO: Check the type of the rel object
        rel_cuba_key = self.DEFAULT_DIRECT_REL if rel is None else rel.cuba_key
        for arg in args:
            self._add_direct(arg, rel_cuba_key)
            arg.add_inverse(self, rel)
        return self

    def _add_direct(self, entity, rel_cuba_key):
        """
        Adds an entity to the current instance with a specific relationship
        :param entity: object to be added
        :param rel_cuba_key: relationship with the entity to add
        """
        # First element, create set
        if rel_cuba_key not in self.keys():
            self.__setitem__(rel_cuba_key, {entity})
        # Element not already there
        elif entity not in self.__getitem__(rel_cuba_key):
            self.__getitem__(rel_cuba_key).add(entity)
        else:
            message = '{!r} is already in the container'
            raise ValueError(message.format(entity))

    def add_inverse(self, entity, rel=None):
        """
        Adds the inverse relationship from self to entity.

        :param entity: container of the normal relationship
        :param rel: direct relationship instance
        """
        inverse_rel = self.DEFAULT_INVERSE_REL if rel is None else rel.inverse
        self._add_direct(entity, inverse_rel)

    def get(self, *uids, rel=None, cuba_key=None):
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(cuba_key),
        get(*uids, rel)

        :param uids: UIDs of the elements
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        :return: list of queried objects, or None, if not found
        """
        output = []

        if cuba_key is None:
            if rel is None:
                # get()
                if not uids:
                    try:
                        output = \
                            list(self.__getitem__(self.DEFAULT_DIRECT_REL))
                    except KeyError:
                        output.append(None)
                # get(*uids)
                else:
                    check_arguments(uuid.UUID, *uids)
                    for uid in uids:
                        output.append(self._get_by_uid(uid))
            # get(rel)
            elif not uids:
                # TODO: check type of rel
                try:
                    output = list(self.__getitem__(rel.cuba_key))
                except KeyError:
                    output.append(None)
            # get(*uids, rel)
            else:
                check_arguments(uuid.UUID, *uids)
                # TODO: check type of rel
                for uid in uids:
                    try:
                        relationship_set = self.__getitem__(rel.cuba_key)
                        output.append(
                            self._get_from_relationship_set(uid,
                                                            relationship_set))
                    except KeyError:
                        output.append(None)
        # get(cuba_key)
        elif (rel is None) and not uids:
            check_arguments(CUBA, cuba_key)
            for relationship_set in self.values():
                for entity in relationship_set:
                    if entity.cuba_key == cuba_key:
                        output.append(entity)
            if not output:
                output.append(None)
        else:
            message = 'Supported calls are get(), get(*uids), get(rel),' \
                      ' get(cuba_key), get(*uids, rel)'
            raise TypeError(message)
        return output

    def _get_by_uid(self, uid):
        """
        Finds an entity in the contained ones by uid.

        :param uid: unique identifier of the wanted entity
        :return: the first entity found with that uid or None
        """
        for relationship_set in self.values():
            for entity in relationship_set:
                if entity.uid == uid:
                    return entity
        return None

    def _get_from_relationship_set(self, uid, relationship_set):
        """
        Finds an entity under a given relationship set by uid.

        :param uid: unique identifier of the wanted entity
        :param relationship_set: set of entities under the same relationship
        :return: the entity found with that uid or None
        """
        for entity in relationship_set:
            if entity.uid == uid:
                return entity

    def remove(self, *args, rel=None, cuba_key=None):
        """
        Removes elements from the DataContainer.
        Expected calls are remove(*uids/DataContainers), remove(rel),
        remove(cuba_key), remove(*uids/DataContainers, rel)

        :param args: UIDs of the elements or the elements themselves
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        """
        modified_relationships = set()

        if cuba_key is None:
            if rel is None:
                # remove(*uids/Datacontainers)
                check_arguments((DataContainer, uuid.UUID), *args)
                for arg in args:
                    removed = False
                    if isinstance(arg, DataContainer):
                        arg = arg.uid
                    # Will remove multiple occurrences
                    for rel_cuba_key, relationship_set in self.items():
                        entity = self._get_from_relationship_set(
                            arg, relationship_set)
                        if entity is not None:
                            entity.remove_inverse(self, rel)
                            relationship_set.remove(entity)
                            modified_relationships.add(rel_cuba_key)
                            removed = True
                    if not removed:
                        message = '{} is not an existing element'
                        raise KeyError(message.format(arg))
            # remove(rel)
            elif not args:
                # TODO: check type of rel
                relationship_set = self.__getitem__(rel.cuba_key)
                # remove the inverse from the entities
                for entity in relationship_set:
                    entity.remove_inverse(self, rel)
                # remove the relationship
                self.__delitem__(rel.cuba_key)
                modified_relationships.add(rel.cuba_key)
            # remove(*uids/Datacontainers, rel)
            else:
                removed = True
                check_arguments((DataContainer, uuid.UUID), *args)
                # TODO: check type of rel
                relationship_set = self.__getitem__(rel.cuba_key)
                for arg in args:
                    removed = False
                    if isinstance(arg, DataContainer):
                        arg = arg.uid

                    entity = self._get_from_relationship_set(arg,
                                                             relationship_set)
                    if entity is not None:
                        entity.remove_inverse(self, rel)
                        relationship_set.remove(entity)
                        modified_relationships.add(rel.cuba_key)
                        removed = True
                if not removed:
                    message = '{} is not an existing elements cuba_key'
                    raise KeyError(message.format(cuba_key))
        # remove(cuba_key)
        elif (rel is None) and not args:
            check_arguments(CUBA, cuba_key)
            # FIXME: Could be more efficient with another relationship mapping
            removed = False
            for rel_cuba_key, relationship_set in self.items():
                for entity in relationship_set.copy():
                    if entity.cuba_key == cuba_key:
                        entity.remove_inverse(self)
                        relationship_set.remove(entity)
                        modified_relationships.add(rel_cuba_key)
                        removed = True
            if not removed:
                message = '{} is not an existing elements cuba_key'
                raise KeyError(message.format(cuba_key))
        else:
            message = 'Supported calls are remove(*uids/DataContainers), ' \
                      'remove(rel), remove(cuba_key), ' \
                      'remove(*uids/DataContainers, rel)'
            raise TypeError(message)

        # remove the empty relationship entries
        for modified_rel in modified_relationships:
            try:
                if not self.__getitem__(modified_rel):
                    self.__delitem__(modified_rel)
            except KeyError:
                # Already removed
                pass

    def remove_inverse(self, entity, rel=None):
        """
        Removes the inverse relationship from self to entity.

        :param entity: container of the normal relationship
        :param rel: direct relationship
        """
        inverse_rel = None
        if rel is None:
            # go through all entities and delete
            for inverse_rel, relationship_set in self.items():
                if entity in relationship_set:
                    relationship_set.remove(entity)
        else:
            inverse_rel = rel.inverse
            relationship_set = self.__getitem__(inverse_rel)
            relationship_set.remove(entity)
        # Erase the relationship CUBA key entry if empty
        if not self.__getitem__(inverse_rel):
            self.__delitem__(inverse_rel)

    def update(self, *args, rel=None):
        """
        Updates the object with the newer objects.

        :param args: entity(ies) to update
        :param rel: relationship where the entities are
        """
        check_arguments('all_simphony_wrappers', *args)
        # update(DataContainers, rel)
        if rel is not None:
            # TODO: check type of rel
            relationship_set = self.__getitem__(rel.cuba_key)
            for arg in args:
                if arg in relationship_set:
                    relationship_set.remove(arg)
                    relationship_set.add(arg)
                else:
                    message = '{} does not exist. Add it first'
                    raise ValueError(message.format(arg))
        # update(DataContainers)
        else:
            for arg in args:
                found = False
                # Updates all instances
                for relationship_set in self.values():
                    if arg in relationship_set:
                        relationship_set.remove(arg)
                        relationship_set.add(arg)
                        found = True
                if not found:
                    message = '{} does not exist. Add it first'
                    raise ValueError(message.format(arg))

    def iter(self):
        """
        Iterates over all the objects contained.
        """
        for relationship_set in self.values():
            for entity in relationship_set:
                yield entity
