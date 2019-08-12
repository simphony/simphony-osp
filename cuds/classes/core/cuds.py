# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
import inspect

from cuds.classes.core.session.core_session import CoreSession
from cuds.utils import check_arguments, filter_cuds_attr
from cuds.classes.generated.relationship import Relationship
from cuds.classes.generated.active_relationship import ActiveRelationship
from cuds.classes.generated.passive_relationship import PassiveRelationship
from cuds.classes.generated.has_part import HasPart
from copy import deepcopy


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
    # TODO: Check that instantiating a wrapper overrides this session
    session = CoreSession()

    def __init__(self):
        """
        Initialization follows the behaviour of the python dict class.
        """
        super().__init__()

        # These are the allowed CUBA keys (faster to convert to set for lookup)
        # self.restricted_keys = frozenset(CUBA)
        self.uid = uuid.uuid4()
        self.session.store(self)

    def __str__(self):
        """
        Redefines the str() for Cuds.

        :return: string with the cuba_key and uid
        """
        return "%s: %s" % (self.cuba_key, self.uid)

    def __setitem__(self, key, value):
        """
        Set/Update the key value only when the key is a relationship.

        :param key: key in the dictionary
        :param value: new value to assign to the key
        :raises ValueError: unsupported key provided (not a relationship)
        """
        if inspect.isclass(key) and issubclass(key, self.ROOT_REL):
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
            if arg.session != self.session:
                arg = arg._clone()
            self._add_direct(arg, rel)
            arg._add_inverse(self, rel)
            # TODO Propagate changes to registry (through session)

            # Recursively add the children to the registry
            if self.session != arg.session:
                self._recursive_store(arg)
        return self

    def get(self, *uids, rel=None, cuba_key=None):
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(cuba_key),
        get(*uids, rel), get(rel, cuba_key).
        If uids are specified, the position of each element in the result
        is determined by to the position of the corresponding uid in the given
        list of uids.
        In this case, the result can contain None values if a given uid is not
        a child of this cuds object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        :return: list of queried objects, or None, if not found
        :rtype: List[Cuds]
        """
        collected_uids, _ = self._get(*uids, rel=rel, cuba_key=cuba_key)
        return list(self._load_entities(collected_uids))

    def update(self, *args):
        """
        Updates the object with the other versions.

        :param args: updated entity(ies)
        """
        check_arguments(Cuds, *args)
        old_objects = self.get(*[arg.uid for arg in args])
        relationship_sets = deepcopy(list(self.values()))

        for arg, old_cuds in zip(args, old_objects):
            found = False
            # Updates all instances
            for relationship_set in relationship_sets:
                if arg.uid in relationship_set:
                    self._recursive_store(arg, old_cuds)
                    found = True
            if not found:
                message = '{} does not exist. Add it first'
                raise ValueError(message.format(arg))

    def remove(self, *args, rel=None, cuba_key=None):
        """
        Removes elements from the Cuds.
        Expected calls are remove(), remove(*uids/Cuds),
        remove(rel), remove(cuba_key), remove(*uids/Cuds, rel),
        remove(rel, cuba_key)

        :param args: UIDs of the elements or the elements themselves
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        """
        uids = [arg.uid if isinstance(arg, Cuds) else arg for arg in args]
        _, relationship_mapping = self._get(*uids, rel=rel, cuba_key=cuba_key)
        if not relationship_mapping:
            raise RuntimeError("Did not remove any Cuds object,"
                               + "because none matched your filter.")
        uid_relationships = list(relationship_mapping.items())
        neighbors = self.session.load(*[uid for uid, _ in uid_relationships])
        for uid_relationship, neighbor in zip(uid_relationships, neighbors):
            uid, relationships = uid_relationship
            for relationship in relationships:
                self._remove_direct(relationship, uid)
                neighbor._remove_inverse(relationship, self.uid)

    def iter(self, *uids, rel=None, cuba_key=None):
        """
        Iterates over the contained elements of a certain type, uid or
        relationship. Expected calls are iter(), iter(*uids), iter(rel),
        iter(cuba_key), iter(*uids, rel), iter(rel, cuba_key).
        If uids are specified, the each element will be yielded in the order
        given by list of uids.
        In this case, elements can be None values if a given uid is not
        a child of this cuds object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        :return: Iterator over of queried objects, or None, if not found
        :rtype: Iterator[Cuds]
        """
        collected_uids, _ = self._get(*uids, rel=rel, cuba_key=cuba_key)
        yield from self._load_entities(collected_uids)

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

    def _recursive_store(self, new_cuds, old_cuds=None, uids_stored=None):
        """Recursively store cuds and all its children.
        One-way relationships and dangling references are fixed.

        :param new_cuds: The Cuds object to store recursively.
        :type new_cuds: Cuds
        :param old_cuds: The old version of the cuds object, defaults to None
        :type old_cuds: Cuds, optional
        :param uids_stored: Remember which cuds objects have already been
            stored in the recursive call, defaults to None
        :type uids_stored: Set[UUID], optional
        :return: The uuids stored by this call
        :rtype: Set[UUID]
        """
        # Store copy in registry and fix parent connections
        new_child_getter = new_cuds
        new_cuds = new_cuds._clone()
        new_cuds.session = self.session
        self._fix_neighbors(new_cuds, old_cuds, self.session)
        stored_cuds = self.session.store(new_cuds)

        # Keep track which cuds objects have already been stored
        if uids_stored is None:
            uids_stored = set()
        uids_stored.add(new_cuds.uid)

        # Recursively add the children
        for outgoing_rel in new_cuds.keys():

            # do not recursively add parents
            if not issubclass(outgoing_rel, ActiveRelationship):
                continue

            # add children not already added
            for child_uid in new_cuds[outgoing_rel].keys():
                if child_uid not in uids_stored:
                    new_child = new_child_getter.get(
                        child_uid, rel=outgoing_rel)[0]
                    old_child = old_cuds.get(child_uid, rel=outgoing_rel)[0] \
                        if old_cuds else None
                    uids_stored |= stored_cuds._recursive_store(new_child,
                                                                old_child,
                                                                uids_stored)
        return uids_stored

    @staticmethod
    def _fix_neighbors(new_cuds, old_cuds, session):
        """Fix all the connections of the neighbors of a Cuds objects
        that is going to be replaced.

        Concerning the relationships of the new cuds object:
        - The new cuds object might have connnections to not available parents
            --> Remove the connection
        - The new cuds object might have connections to not availbe children
            --> Do nothing as the children will be recursively added

        Concerning the relationships of the neighbors:
        - A parent of the old cuds is not a parent in the new one:
            --> Add a relationship to the new cuds to the parent
        - A child of the old cuds is not a parent in the new one:
            --> Remove the relationship of the child
        - A cuds object is suddenly a parent after the replacement
            --> Add the inverse relationship to the new parent
        - A cuds object is suddenly a child after the replacement
            --> Do nothing since the children will get recursively updated

        :param new_cuds: Cuds object that will replace the old one
        :type new_cuds: Cuds
        :param old_cuds: Cuds object that will be replaced by a new one.
            Can be None if the new Cuds object does not replace any object.
        :type old_cuds: Cuds
        :param session: The session where the adjustments should take place.
        :type session: Session
        """
        old_cuds = old_cuds or dict()
        Cuds._fix_new_neighbors(new_cuds, old_cuds, session)
        Cuds._fix_old_neighbors(new_cuds, old_cuds, session)

    @staticmethod
    def _fix_new_neighbors(new_cuds, old_cuds, session):
        """Fix the relationships of Cuds objects, that are neighbors
        of a Cuds object, that has been added from another session or
        will replace a cuds object.

        :param new_cuds: Cuds object that will replace the old one
        :type new_cuds: Cuds
        :param old_cuds: Cuds object that will be replaced by a new one.
            Can be None if the new Cuds object does not replace any object.
        :type old_cuds: Cuds
        :param session: The session where the adjustments should take place.
        :type session: Session
        """
        # TODO avoid circular imports
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING

        # Iterate over all new parents.
        # Children get recursively updated, so no need to manipulate them.
        delete_relationships = set()
        for relationship in new_cuds.keys():
            if not issubclass(relationship, PassiveRelationship):
                continue
            inverse = CUBA_MAPPING[relationship.inverse]

            # Get all the parents that were no parent before
            old_parent_uids = set()
            if relationship in old_cuds:
                old_parent_uids = old_cuds[relationship].keys()
            new_parent_uids = list(
                new_cuds[relationship].keys() - old_parent_uids)
            new_parents = session.load(*new_parent_uids)

            # Iterate over the new parents
            for parent_uid, parent in zip(new_parent_uids, new_parents):

                # Delete connection to parent if parent is not present
                if parent is None:
                    del new_cuds[relationship][parent_uid]
                    if len(new_cuds[relationship]) == 0:
                        delete_relationships.add(relationship)
                    continue

                # Add the inverse to the parent
                if inverse not in parent:
                    parent[inverse] = dict()

                # TODO push these changes to the sessions buffers
                parent[inverse].update({new_cuds.uid: new_cuds.cuba_key})
        for delete in delete_relationships:
            del new_cuds[delete]

    @staticmethod
    def _fix_old_neighbors(new_cuds, old_cuds, session):
        """Fix the relationships of Cuds objects that are no longer neighbors after
        a new Cuds object has been added from another session /
        a Cuds object has been updated.

        :param new_cuds: Cuds object that will replace the old one
        :type new_cuds: Cuds
        :param old_cuds: Cuds object that will be replaced by a new one.
            Can be None if the new Cuds object does not replace any object.
        :type old_cuds: Cuds
        :param session: The session where the adjustments should take place.
        :type session: Session
        """
        # TODO avoid circular imports
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        # iterate over all previous neighbors, that are no longer neighbor.
        for relationship in old_cuds.keys():
            inverse = CUBA_MAPPING[relationship.inverse]

            # get all the neighbors that are no longer neigbor
            new_neighbor_uids = set()
            if relationship in new_cuds:
                new_neighbor_uids = new_cuds[relationship].keys()

            # delete the inverse if neighbors are children
            if issubclass(relationship, ActiveRelationship):
                old_children = session.load(
                    *list(old_cuds[relationship].keys() - new_neighbor_uids))
                for child in old_children:
                    if inverse in child:
                        child._remove_direct(inverse, new_cuds.uid)

            # if neighbor is parent, add missing relationships
            else:
                new_parents = session.load(
                    *list(new_neighbor_uids - old_cuds[relationship].keys()))
                if relationship not in new_cuds:
                    new_cuds[relationship] = dict()
                for (uid, cuba_key), parent in \
                        zip(old_cuds[relationship].items(), new_parents):
                    if parent is not None:
                        new_cuds[relationship][uid] = cuba_key

    def _add_direct(self, entity, rel, error_if_already_there=True):
        """
        Adds an entity to the current instance with a specific relationship
        :param entity: object to be added
        :param rel: relationship with the entity to add
        """
        # First element, create set
        if rel not in self.keys():
            self.__setitem__(rel, {entity.uid: entity.cuba_key})
        # Element not already there
        elif entity.uid not in self.__getitem__(rel):
            self.__getitem__(rel)[entity.uid] = entity.cuba_key
        elif error_if_already_there:
            message = '{!r} is already in the container'
            raise ValueError(message.format(entity))

    def _add_inverse(self, entity, rel):
        """
        Adds the inverse relationship from self to entity.

        :param entity: container of the normal relationship
        :param rel: direct relationship instance
        """
        # TODO avoid circular imports
        from ..generated.cuba_mapping import CUBA_MAPPING
        inverse_rel = CUBA_MAPPING[rel.inverse]
        self._add_direct(entity, inverse_rel, error_if_already_there=False)

    def _get(self, *uids, rel=None, cuba_key=None):
        """
        Returns the uid of contained elements of a certain type, uid or
        relationship.
        Expected calls are get(), get(*uids), get(rel), get(cuba_key),
        get(*uids, rel), get(rel, cuba_key).
        If uids are specified, the result is the input, but
        non-available uids are replaced by None.

        :param uids: UIDs of the elements
        :param rel: class of the relationship
        :param cuba_key: CUBA key of the subelements
        :return: list of uids, or None, if not found
        :rtype: List[UUID]
        """
        if uids and cuba_key is not None:
            raise RuntimeError("Do not specify both uids and cuba_key")

        if uids:
            check_arguments(uuid.UUID, *uids)

        if rel is not None and rel not in self.keys():
            return ([], dict()) if not uids else ([None] * len(uids), dict())

        # consider either only given relationship or all relationships.
        consider_relationships = [rel]
        if rel is None:
            consider_relationships = list(self.keys())
        if uids:
            return self._get_by_uids(uids, consider_relationships)
        return self._get_by_cuba_key(cuba_key, consider_relationships)

    def _get_by_uids(self, uids, relationships):
        """Check for each given uid if it is connected to self by a relationship.
        If not, replace it with None.
        Return a mapping from uids to the set of relationships,
        which connect self and the cuds object with the uid.

        :param uids: The uids to check.
        :type uids: List[UUID]
        :param relationships: Only consider these relationships
        :type relationships: List[Relationship]
        :return: list of found uids, None for not found UUIDs
            + Mapping from UUIDs to relationships, which connect self to the
            respctive Cuds object.
        :rtype: Tuple[List[UUID], Dict[UUID, Set[Relationship]]]
        """
        not_found_uids = dict(enumerate(uids)) if uids else None
        relationship_mapping = dict()
        for relationship in relationships:

            # Uids are given.
            # Check which occur as object of current relation.
            found_uid_indexes = set()
            for i, uid in not_found_uids.items():
                if uid in self.__getitem__(relationship):
                    found_uid_indexes.add(i)
                    if uid not in relationship_mapping:
                        relationship_mapping[uid] = set()
                    relationship_mapping[uid].add(relationship)
            for i in found_uid_indexes:
                del not_found_uids[i]

        collected_uids = [(uid if i not in not_found_uids else None)
                          for i, uid in enumerate(uids)]
        return collected_uids, relationship_mapping

    def _get_by_cuba_key(self, cuba_key, relationships):
        """Get the cuds with given cuba_key that are connected to self
        with any of the given relationships.

        :param cuba_key: Filter by the given cuba_key. None means no filter.
        :type cuba_key: CUBA
        :param relationships: Filter by list of relationships
        :type relationships: List[Relationship]
        :return: The uids of the found Cuds + Mapping from uuid to set of
            relationsships that connect self with the respective cuds.
        :rtype: Tuple[List[UUID], Dict[UUID, Set[Relationship]]]
        """
        relationship_mapping = dict()
        for relationship in relationships:

            # Collect all uids who are object of the current relationship.
            # Possibly filter by Cuba-Key.
            for uid, cuba in self[relationship].items():
                if cuba_key is None or cuba == cuba_key:
                    if uid not in relationship_mapping:
                        relationship_mapping[uid] = set()
                    relationship_mapping[uid].add(relationship)
        return list(relationship_mapping.keys()), relationship_mapping

    def _load_entities(self, uids):
        """Load the entities of the given uids from the session.
        Each in entity is at the same position in the result as
        the corresponding uid in the given uid list.
        If the given uids contain None values, there will be
        None values at the same postion in the result.

        :param uids: The uids to fetch from the session.
        :type uids: List[UUID]
        :return: The loaded entities
        :rtype: List[Cuds]
        """
        without_none = [uid for uid in uids if uid is not None]
        entities = self.session.load(*without_none)
        for uid in uids:
            if uid is None:
                yield None
            else:
                yield next(entities)

    def _remove_direct(self, relationship, uid):
        del self[relationship][uid]
        if not self[relationship]:
            del self[relationship]

    def _remove_inverse(self, relationship, uid):
        # TODO avoid circular imports
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        inverse = CUBA_MAPPING[relationship.inverse]
        self._remove_direct(inverse, uid)

    def _clone(self):
        """Avoid that the session gets copied.

        :return: A copy of self with the same session
        :rtype: Cuds
        """
        session = self.session
        if "session" in self.__dict__:
            del self.__dict__["session"]
        clone = deepcopy(self)
        clone.session = session
        return clone
