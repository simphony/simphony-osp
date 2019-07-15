# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid

from .session.core_session import CoreSession
from ...utils import check_arguments, filter_cuds_attr
from ..generated.cuba import CUBA
from ..generated.relationship import Relationship
from ..generated.has_part import HasPart


class Cuds(dict):
    """
    A Common Universal Data Structure

    The Cuds object is implemented as a python dictionary whose keys
    are the relationship between the element and the member.

    The instances of the contained elements are accessible
    through the shared session
    """
    DEFAULT_REL = HasPart
    ROOT_REL = Relationship
    cuba_key = None
    session = CoreSession()

    def __init__(self):
        """
        Initialization follows the behaviour of the python dict class.
        """
        super().__init__()

        # These are the allowed CUBA keys (faster to convert to set for lookup)
        # self.restricted_keys = frozenset(CUBA)
        self.uid = uuid.uuid4()
        self.session.add(self)

    def __str__(self):
        """
        Redefines the str() for Cuds.

        :return: string with the uid, cuba_key and first level children
        """
        # FIXME: Update to new design
        items = self._str_attributes()

        for name, relationship_set in self.items():
            items.append(self._str_relationship_set(name, relationship_set))

        return "{\n  " + ",\n  ".join(items) + "\n}"

    def _str_attributes(self):
        """
        Serialises the relevant attributes from the instance.

        :return: list with the attributes in a key-value form string
        """
        attributes = []
        for attribute in sorted(filter_cuds_attr(self)):
            attributes.append(attribute + ": " + str(getattr(self, attribute)))

        return attributes

    @staticmethod
    def _str_relationship_set(rel_key, rel_set):
        """
        Serialises a relationship set with the given name in a key-value form.

        :param rel_key: CUBA key of the relationship
        :param rel_set: set of the objects contained under that relationship
        :return: string with the uids of the contained elements
        """
        elements = [str(element.uid) for element in rel_set]

        return str(rel_key) + ": {\n\t" + ",\n\t".join(elements) + "\n  }"

    def __setitem__(self, key, value):
        """
        Set/Update the key value only when the key is a relationship.

        :param key: key in the dictionary
        :param value: new value to assign to the key
        :raises ValueError: unsupported key provided (not a relationship)
        """
        if issubclass(key, self.ROOT_REL):
            super().__setitem__(key, value)
        else:
            message = 'Key {!r} is not in the supported relationships'
            raise ValueError(message.format(key))

    def __hash__(self):
        """
        Makes Cuds objects hashable.
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
        check_arguments(Cuds, *args)
        if rel is None:
            rel = self.DEFAULT_REL
        for arg in args:
            self._add_direct(arg, rel)
            arg.add_inverse(self, rel)
            # TODO: Propagate changes to registry (through session)
            if self.session != arg.session:
                self.session.add(arg)
        return self

    def _add_direct(self, entity, rel):
        """
        Adds an entity to the current instance with a specific relationship
        :param entity: object to be added
        :param rel: relationship with the entity to add
        """
        # First element, create set
        if rel not in self.keys():
            self.__setitem__(rel, {entity.uid: entity.cuba_key})
        # Element not already there
        elif entity not in self.__getitem__(rel):
            self.__getitem__(rel)[entity.uid] = entity.cuba_key
        else:
            message = '{!r} is already in the container'
            raise ValueError(message.format(entity))

    def add_inverse(self, entity, rel):
        """
        Adds the inverse relationship from self to entity.

        :param entity: container of the normal relationship
        :param rel: direct relationship instance
        """
        inverse_rel = rel.inverse
        self._add_direct(entity, inverse_rel)

    def get(self, *uids, rel=None, cuba_key=None):
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(cuba_key),
        get(*uids, rel), get(rel, cuba_key)

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
                        # Unique elements
                        unique = set.union(*self.values())
                        output = list(unique)
                    # No elements
                    except TypeError:
                        output.append(None)
                # get(*uids)
                else:
                    check_arguments(uuid.UUID, *uids)
                    for uid in uids:
                        output.append(self._get_by_uid(uid))
            # get(rel)
            elif not uids:
                try:
                    output = list(self.__getitem__(rel))
                except KeyError:
                    output.append(None)
            # get(*uids, rel)
            else:
                check_arguments(uuid.UUID, *uids)
                for uid in uids:
                    try:
                        relationship_set = self.__getitem__(rel)
                        output.append(
                            self._get_from_relationship_set(uid,
                                                            relationship_set))
                    except KeyError:
                        output.append(None)
        elif not uids:
            # get(cuba_key)
            if rel is None:
                check_arguments(CUBA, cuba_key)
                for relationship_set in self.values():
                    for entity in relationship_set:
                        if entity.cuba_key == cuba_key:
                            output.append(entity)
                if not output:
                    output.append(None)
            # get(rel, cuba_key)
            else:
                try:
                    relationship_set = self.__getitem__(rel)
                    for entity in relationship_set:
                        if entity.cuba_key == cuba_key:
                            output.append(entity)
                except KeyError:
                    output.append(None)
        else:
            message = 'Supported calls are get(), get(*uids), get(rel),' \
                      ' get(cuba_key), get(*uids, rel), get(rel, cuba_key)'
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
        Removes elements from the Cuds.
        Expected calls are remove(), remove(*uids/DataContainers),
        remove(rel), remove(cuba_key), remove(*uids/DataContainers, rel),
        remove(rel, cuba_key)

        :param args: UIDs of the elements or the elements themselves
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        """
        modified_relationships = set()

        if cuba_key is None:
            if rel is None:
                # remove()
                if not args:
                    # Remove inverse from all
                    for entity in self.iter():
                        entity.remove_inverse(self)
                    # Remove all
                    self.clear()
                else:
                    # remove(*uids/Datacontainers)
                    check_arguments((Cuds, uuid.UUID), *args)
                    for arg in args:
                        removed = False
                        if isinstance(arg, Cuds):
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
                check_arguments((Cuds, uuid.UUID), *args)
                relationship_set = self.__getitem__(rel.cuba_key)
                for arg in args:
                    removed = False
                    if isinstance(arg, Cuds):
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
        elif not args:
            # remove(cuba_key)
            if rel is None:
                check_arguments(CUBA, cuba_key)
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
            # remove(rel, cuba_key)
            else:
                relationship_set = self.__getitem__(rel.cuba_key)
                for entity in relationship_set.copy():
                    if entity.cuba_key == cuba_key:
                        entity.remove_inverse(self, rel)
                        relationship_set.remove(entity)
                        modified_relationships.add(rel.cuba_key)

        else:
            message = 'Supported calls are remove(*uids/DataContainers), ' \
                      'remove(rel), remove(cuba_key), remove(rel, cuba_key)' \
                      ', remove(*uids/DataContainers, rel)'
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
            # FIXME: Could be more efficient with different inverse mapping
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

    def update(self, *args):
        """
        Updates the object with the other versions.

        :param args: updated entity(ies)
        """
        check_arguments('all_simphony_wrappers', *args)

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
