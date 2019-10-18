# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

# from __future__ import annotations
import uuid
import inspect
from typing import Union, Type, List, Iterator, Dict

from cuds.generator.ontology_datatypes import convert_to
from cuds.session.core_session import CoreSession
from cuds.classes.relationship_tree import RelationshipTree
from cuds.utils import check_arguments, clone_cuds_object, \
    create_from_cuds_object, get_neighbour_diff
from cuds.generator.settings import DEFAULT as DEFAULT_CUDS_SETTINGS
from cuds.classes.generated.relationship import Relationship
from cuds.classes.generated.cuba import CUBA
from cuds.classes.generated.active_relationship import ActiveRelationship
from copy import deepcopy


class Cuds(dict):
    """
    A Common Universal Data Structure

    The Cuds object is implemented as a python dictionary whose keys
    are the relationship between the element and the member.

    The instances of the contained elements are accessible
    through the shared session
    """
    DEFAULT_REL = None
    ROOT_REL = Relationship
    cuba_key = None
    supported_relationships = dict()
    CUDS_SETTINGS = deepcopy(DEFAULT_CUDS_SETTINGS)
    _session = CoreSession()

    def __init__(self, uid: uuid.UUID = None):
        """
        Initialization follows the behavior of the python dict class.

        :param uid: Specify a unique identifier. If none, given a random
            uid will be created.
        :type uid: UUID
        """
        super().__init__()
        from cuds.classes.generated import PARSED_SETTINGS
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        Cuds.CUDS_SETTINGS.update(PARSED_SETTINGS)
        Cuds.DEFAULT_REL = CUBA_MAPPING[
            CUBA(Cuds.CUDS_SETTINGS["default_relationship"])]
        self.__uid = uuid.uuid4() if uid is None else convert_to(uid, "UUID")
        # store the hierarchical order of the relationships
        self._relationship_tree = RelationshipTree(self.ROOT_REL)
        self.session.store(self)

    @property
    def uid(self) -> uuid.UUID:
        return self.__uid

    @property
    def session(self):
        return self._session

    def __str__(self) -> str:
        """
        Redefines the str() for Cuds.

        :return: string with the cuba_key and uid.
        """
        return "%s: %s" % (self.cuba_key, self.uid)

    def __getitem__(self, key):
        self.session._notify_read(self)
        return super().__getitem__(key)

    # OVERRIDE
    def __delitem__(self, key: Type[Relationship]):
        """Delete a relationship from the Cuds.

        :param key: The relationship to remove
        :type key: Type[Relationship]
        :raises ValueError: The given key is not a relationship.
        """
        self.session._notify_read(self)
        if inspect.isclass(key) and issubclass(key, self.ROOT_REL):
            super().__delitem__(key)
            self._relationship_tree.remove(key)
            self.session._notify_update(self)
        else:
            message = 'Key {!r} is not in the supported relationships'
            raise ValueError(message.format(key))

    def __setitem__(self, key: Type[Relationship], value: dict):
        """
        Set/Update the key value only when the key is a relationship.

        :param key: key in the dictionary
        :type key: Type[Relationship]
        :param value: new value to assign to the key
        :type value: dict
        :raises ValueError: unsupported key provided (not a relationship)
        """
        self.session._notify_read(self)
        if inspect.isclass(key) and issubclass(key, self.ROOT_REL) \
                and isinstance(value, dict):
            for _, cuba_key in value.items():
                self._check_valid_add(cuba_key, key)
            # Any changes to the dict should be sent to the session
            super().__setitem__(key, NotifyDict(value,
                                                cuds_object=self,
                                                rel=key))
            self._relationship_tree.add(key)
            self.session._notify_update(self)
        else:
            message = 'Key {!r} is not in the supported relationships'
            raise ValueError(message.format(key))

    def __hash__(self) -> int:
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

    @classmethod
    def get_attributes(cls, skip: List[str] = None) -> List[str]:
        """Get all the attributes of the cuds_object.

        :param skip: Do only return attributes not specified here,
            defaults to None
        :type skip: List[str], optional
        :return: A list of the attributes
        :rtype: List[str]
        """
        skip = skip or []
        return [x for x in inspect.getfullargspec(cls.__init__).args
                if x not in skip][1:]

    @classmethod
    def get_datatypes(cls) -> Dict[str, str]:
        """Get the datatypes of the attributes of the cuds_object.

        :return: The datatypes of the attributes as a mapping
            from attribute to datatype
        :rtype: Dict[str, str]
        """
        return inspect.getfullargspec(cls.__init__).annotations

    def contains(self, relationship):
        """Check whether the given relationship or a subrelationship is contained
        in this cuds object

        :param relationship: The relationship to look for.
        :type relationship: Type[Relationship]
        :return: Whether the relationship or a subrelationship has been found.
        :rtype: bool
        """
        return self._relationship_tree.contains(relationship)

    def add(self,
            *args: "Cuds",
            rel: Type[Relationship] = None) -> Union["Cuds", List["Cuds"]]:
        """
        Adds (a) cuds(s) to their respective CUBA key relationship.
        Before adding, check for invalid keys to avoid inconsistencies later.

        :param args: object(s) to add
        :type args: Cuds
        :param rel: class of the relationship between the objects
        :type rel: Type[Relationship]
        :return: The added object(s)
        :rtype: Union[Cuds, List[Cuds]]
        :raises ValueError: adding an element already there
        """
        check_arguments(Cuds, *args)
        if rel is None:
            rel = self.DEFAULT_REL
        result = list()
        old_objects = self._session.load(
            *[arg.uid for arg in args if arg.session != self.session])
        for arg in args:
            # Recursively add the children to the registry
            if rel in self and arg.uid in self[rel]:
                message = '{!r} is already in the container'
                raise ValueError(message.format(arg))
            if self.session != arg.session:
                arg = self._recursive_store(arg, next(old_objects))

            self._add_direct(arg, rel)
            arg._add_inverse(self, rel)
            result.append(arg)
        return result[0] if len(args) == 1 else result

    def get(self,
            *uids: uuid.UUID,
            rel: Type[Relationship] = ActiveRelationship,
            cuba_key: CUBA = None) -> Union["Cuds", List["Cuds"]]:
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(cuba_key),
        get(*uids, rel), get(rel, cuba_key).
        If uids are specified, the position of each element in the result
        is determined by to the position of the corresponding uid in the given
        list of uids.
        In this case, the result can contain None values if a given uid is not
        a child of this cuds_object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements
        :param rel: Only return cuds_object which are connected by subclass of
            given relationship.
        :type rel: Type[Relationship]
        :param cuba_key: CUBA key of the subelements
        :type cuba_key: CUBA
        :return: the queried objects, or None, if not found
        :rtype: Union[Cuds, List[Cuds]]
        """
        collected_uids = self._get(*uids, rel=rel, cuba_key=cuba_key)
        result = list(self._load_cuds_objects(collected_uids))
        if len(uids) == 1:
            return result[0]
        return result

    def update(self, *args: "Cuds") -> List["Cuds"]:
        """
        Updates the object with the other versions.

        :param args: updated entity(ies)
        :type args: Cuds
        :return: The updated cuds_object.
        :rtype: Union[Cuds, List[Cuds]]
        """
        check_arguments(Cuds, *args)
        old_objects = self.get(*[arg.uid for arg in args])
        if len(args) == 1:
            old_objects = [old_objects]
        if any(x is None for x in old_objects):
            message = 'Cannot update because cuds_object not added.'
            raise ValueError(message)

        result = list()
        for arg, old_cuds_object in zip(args, old_objects):
            # Updates all instances
            result.append(self._recursive_store(arg, old_cuds_object))

        if len(args) == 1:
            return result[0]
        return result

    def remove(self,
               *args: Union["Cuds", uuid.UUID],
               rel: Type[Relationship] = ActiveRelationship,
               cuba_key: CUBA = None):
        """
        Removes elements from the Cuds.
        Expected calls are remove(), remove(*uids/Cuds),
        remove(rel), remove(cuba_key), remove(*uids/Cuds, rel),
        remove(rel, cuba_key)

        :param args: UIDs of the elements or the elements themselves
        :type args: Union[Cuds, UUID]
        :param rel: Only remove cuds_object which are connected by subclass of
            given relationship
        :type rel: Type[Relationship]
        :param cuba_key: CUBA key of the subelements
        :type cuba_key: CUBA
        """
        uids = [arg.uid if isinstance(arg, Cuds) else arg for arg in args]

        # Get mapping from uids to connecting relationships
        _, relationship_mapping = self._get(*uids, rel=rel, cuba_key=cuba_key,
                                            return_mapping=True)
        if not relationship_mapping:
            raise RuntimeError("Did not remove any Cuds object, "
                               + "because none matched your filter.")
        uid_relationships = list(relationship_mapping.items())

        # load all the neighbours to delete and remove inverse relationship
        neighbours = self.session.load(*[uid for uid, _ in uid_relationships])
        for uid_relationship, neighbour in zip(uid_relationships, neighbours):
            uid, relationships = uid_relationship
            for relationship in relationships:
                self._remove_direct(relationship, uid)
                neighbour._remove_inverse(relationship, self.uid)

    def iter(self,
             *uids: uuid.UUID,
             rel: Type[Relationship] = ActiveRelationship,
             cuba_key: CUBA = None) -> Iterator["Cuds"]:
        """
        Iterates over the contained elements of a certain type, uid or
        relationship. Expected calls are iter(), iter(*uids), iter(rel),
        iter(cuba_key), iter(*uids, rel), iter(rel, cuba_key).
        If uids are specified, the each element will be yielded in the order
        given by list of uids.
        In this case, elements can be None values if a given uid is not
        a child of this cuds_object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements.
        :type uids: UUID
        :param rel: class of the relationship.
        :type rel: Type[relationship]
        :param cuba_key: CUBA key of the subelements.
        :type cuba_key: CUBA
        :return: Iterator over of queried objects, or None, if not found.
        :rtype: Iterator[Cuds]
        """
        collected_uids = self._get(*uids, rel=rel, cuba_key=cuba_key)
        yield from self._load_cuds_objects(collected_uids)

    def _str_attributes(self):
        """
        Serializes the relevant attributes from the instance.

        :return: list with the attributes in a key-value form string
        """
        attributes = []
        for attribute in sorted(self.get_attributes(skip=["session"])):
            attributes.append(attribute + ": " + str(getattr(self, attribute)))

        return attributes

    @staticmethod
    def _str_relationship_set(rel_key, rel_set):
        """
        Serializes a relationship set with the given name in a key-value form.

        :param rel_key: CUBA key of the relationship
        :type rel_key: CUBA
        :param rel_set: set of the objects contained under that relationship
        :type rel_set: Set[Cuds]
        :return: string with the uids of the contained elements
        :rtype: str
        """
        elements = [str(element.uid) for element in rel_set]

        return str(rel_key) + ": {\n\t" + ",\n\t".join(elements) + "\n  }"

    def _recursive_store(self, new_cuds_object, old_cuds_object=None):
        """Recursively store cuds_object and all its children.
        One-way relationships and dangling references are fixed.

        :param new_cuds_object: The Cuds object to store recursively.
        :type new_cuds_object: Cuds
        :param old_cuds_object: The old version of the cuds_object,
            defaults to None
        :type old_cuds_object: Cuds, optional
        :rtype: Set[UUID]
        """
        # add new_cuds_object to self and replace old_cuds_object
        queue = [(self, new_cuds_object, old_cuds_object)]
        uids_stored = {new_cuds_object.uid, self.uid}
        missing = dict()
        result = None
        while queue:

            # Store copy in registry
            add_to, new_cuds_object, old_cuds_object = queue.pop(0)
            if new_cuds_object.uid in missing:
                del missing[new_cuds_object.uid]
            old_cuds_object = clone_cuds_object(old_cuds_object)
            new_child_getter = new_cuds_object
            new_cuds_object = create_from_cuds_object(new_cuds_object,
                                                      add_to.session)
            # fix the connections to the neighbours
            add_to._fix_neighbours(new_cuds_object, old_cuds_object,
                                   add_to.session, missing)
            result = result or new_cuds_object

            for outgoing_rel in new_cuds_object.keys():

                # do not recursively add parents
                if not issubclass(outgoing_rel, ActiveRelationship):
                    continue

                # add children not already added
                for child_uid in new_cuds_object[outgoing_rel].keys():
                    if child_uid not in uids_stored:
                        new_child = new_child_getter.get(
                            child_uid, rel=outgoing_rel)
                        old_child = old_cuds_object.get(child_uid,
                                                        rel=outgoing_rel) \
                            if old_cuds_object else None
                        queue.append((new_cuds_object, new_child, old_child))
                        uids_stored.add(new_child.uid)

        # perform the deletion
        for uid in missing:
            for cuds_object, rel in missing[uid]:
                del cuds_object[rel][uid]
                if not cuds_object[rel]:
                    del cuds_object[rel]
        return result

    @staticmethod
    def _fix_neighbours(new_cuds_object, old_cuds_object, session, missing):
        """Fix all the connections of the neighbours of a Cuds objects
        that is going to be replaced.

        Behavior when neighbours change:

        - new_cuds_object has parents, that weren't parents of old_cuds_object.
            - the parents are already stored in the session of old_cuds_object.
            - they are not already stored in the session of old_cuds_object.
            --> Add references between new_cuds_object and the parents that are
                already in the session.
            --> Delete references between new_cuds_object and parents that are
                not available.
        - new_cuds_object has children, that weren't
                children of old_cuds_object.
            --> add/update them recursively.

        - A parent of old_cuds_object is no longer a parent of new_cuds_object.
        --> Add a relationship between that parent and the new cuds_object.
        - A child of old_cuds_object is no longer a child of new_cuds_object.
        --> Remove the relationship between child and new_cuds_object.

        :param new_cuds_object: Cuds object that will replace the old one
        :type new_cuds_object: Cuds
        :param old_cuds_object: Cuds object that will be replaced by a new one.
            Can be None if the new Cuds object does not replace any object.
        :type old_cuds_object: Cuds
        :param session: The session where the adjustments should take place.
        :type session: Session
        :param missing: dictionary that will be populated with connections
            to objects, that are currently not available in the new session.
            The recursive add might add it later.
        :type missing: dict
        """
        old_cuds_object = old_cuds_object or dict()

        # get the parents that got parents after adding the new Cuds
        new_parent_diff = get_neighbour_diff(
            new_cuds_object, old_cuds_object, mode="non-active")
        # get the neighbours that were neighbours
        # before adding the new cuds_object
        old_neighbour_diff = get_neighbour_diff(old_cuds_object,
                                                new_cuds_object)

        # Load all the cuds_objects of the session
        cuds_objects = session.load(
            *[uid for uid, _ in new_parent_diff + old_neighbour_diff])

        # Perform the fixes
        Cuds._fix_new_parents(new_cuds_object=new_cuds_object,
                              new_parents=cuds_objects,
                              new_parent_diff=new_parent_diff,
                              missing=missing)
        Cuds._fix_old_neighbours(new_cuds_object=new_cuds_object,
                                 old_cuds_object=old_cuds_object,
                                 old_neighbours=cuds_objects,
                                 old_neighbour_diff=old_neighbour_diff)

    @staticmethod
    def _fix_new_parents(new_cuds_object, new_parents,
                         new_parent_diff, missing):
        """Fix the relationships beetween the added Cuds objects and
        the parents of the added Cuds object.

        :param new_cuds_object: The added Cuds object
        :type new_cuds_object: Cuds
        :param new_parents: The new parents of the added Cuds object
        :type new_parents: Iterator[Cuds]
        :param new_parent_diff: The uids of the new parents and the relations
            they are connected with
        :type new_parent_diff: List[Tuple[UID, Relationship]]
        :param missing: dictionary that will be populated with connections
            to objects, that are currently not available in the new session.
            The recursive add might add it later.
        :type missing: dict
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING

        # Iterate over the new parents
        for (parent_uid, relationship), parent in zip(new_parent_diff,
                                                      new_parents):
            if issubclass(relationship, ActiveRelationship):
                continue
            inverse = CUBA_MAPPING[relationship.inverse]
            # Delete connection to parent if parent is not present
            if parent is None:
                if parent_uid not in missing:
                    missing[parent_uid] = list()
                missing[parent_uid].append((new_cuds_object, relationship))
                continue

            # Add the inverse to the parent
            if inverse not in parent:
                parent[inverse] = dict()

            parent[inverse][new_cuds_object.uid] = new_cuds_object.cuba_key

    @staticmethod
    def _fix_old_neighbours(new_cuds_object, old_cuds_object, old_neighbours,
                            old_neighbour_diff):
        """Fix the relationships beetween the added Cuds objects and
        the Cuds object that were previously neighbours.

        :param new_cuds_object: The added Cuds object
        :type new_cuds_object: Cuds
        :param old_cuds_object: The Cuds object that is going to be replaced
        :type old_cuds_object: Union[Cuds, None]
        :param old_neighbours: The Cuds object that were neighbours before the
            replacement.
        :type old_neighbours: Iterator[Cuds]
        :param old_neighbour_diff: The uids of the old neigbors and the
            relations they are connected with
        :type old_neighbour_diff: List[Tuple[UID, Relationship]]
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING

        # iterate over all old neighbours.
        for (neighbour_uid, relationship), neighbour in zip(old_neighbour_diff,
                                                            old_neighbours):
            inverse = CUBA_MAPPING[relationship.inverse]

            # delete the inverse if neighbours are children
            if issubclass(relationship, ActiveRelationship):
                if inverse in neighbour:
                    neighbour._remove_direct(inverse, new_cuds_object.uid)

            # if neighbour is parent, add missing relationships
            else:
                if relationship not in new_cuds_object:
                    new_cuds_object[relationship] = dict()
                for (uid, cuba_key), parent in \
                        zip(old_cuds_object[relationship].items(), neighbour):
                    if parent is not None:
                        new_cuds_object[relationship][uid] = cuba_key

    def _add_direct(self, cuds_object, rel):
        """
        Adds an cuds_object to the current instance
            with a specific relationship
        :param cuds_object: object to be added
        :type cuds_object: Cuds
        :param rel: relationship with the cuds_object to add
        :type rel: Type[Relationships]
        """
        # First element, create set
        if rel not in self.keys():
            self.__setitem__(rel, {cuds_object.uid: cuds_object.cuba_key})
        # Element not already there
        elif cuds_object.uid not in self[rel]:
            self[rel][cuds_object.uid] = cuds_object.cuba_key

    def _check_valid_add(self, cuba_key, rel):
        """Check if adding should be allowed.

        :param cuba_key: The cuba key of the cuds_object to add.
        :type cuba_key: Cuds
        :param rel: Relationship with the cuds_object to add.
        :type rel: Relationship
        :raises ValueError: Add is illegal.
        """
        if not Cuds.CUDS_SETTINGS["check_relationship_supported"]:
            return

        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        for supported_relationships, supported_cuds_objects in \
                self.supported_relationships.items():
            if issubclass(rel, CUBA_MAPPING[supported_relationships]):
                for supported_entity in supported_cuds_objects:
                    if issubclass(CUBA_MAPPING[cuba_key],
                                  CUBA_MAPPING[supported_entity]):
                        return

        raise ValueError(
            ("Cannot add %s to %s with relationship %s: "
                + "Invalid relationship or object. Check the ontology!")
            % (cuba_key, self.cuba_key, rel.cuba_key))

    def _add_inverse(self, cuds_object, rel):
        """
        Adds the inverse relationship from self to cuds_object.

        :param cuds_object: container of the normal relationship
        :param rel: direct relationship instance
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        inverse_rel = CUBA_MAPPING[rel.inverse]
        self._add_direct(cuds_object, inverse_rel)

    def _get(self, *uids, rel=None, cuba_key=None, return_mapping=False):
        """
        Returns the uid of contained elements of a certain type, uid or
        relationship.
        Expected calls are _get(), _get(*uids), _get(rel),_ get(cuba_key),
        _get(*uids, rel), _get(rel, cuba_key).
        If uids are specified, the result is the input, but
        non-available uids are replaced by None.

        :param uids: UIDs of the elements
        :type uids
        :param rel: class of the relationship, optional
        :type rel: Type[Relationship]
        :param cuba_key: CUBA key of the subelements, optional
        :type cuba_key: CUBA
        :param return_mapping: whether to return a mapping from
            uids to relationships, that connect self with the uid.
        :type return_mapping: bool
        :return: list of uids, or None, if not found.
            (+ Mapping from UUIDs to relationships, which connect self to the
            respective Cuds object.)
        :rtype: List[UUID] (+ Dict[UUID, Set[Relationship]])
        """
        if uids and cuba_key is not None:
            raise RuntimeError("Do not specify both uids and cuba_key")

        if uids:
            check_arguments(uuid.UUID, *uids)

        self.session._notify_read(self)
        # consider either given relationship and subclasses
        # or all relationships.
        if rel is None:
            consider_relationships = list(self.keys())
        else:
            consider_relationships = self._relationship_tree \
                .get_subrelationships(rel)

        # return empty list if no element of given relationship is available.
        if not consider_relationships and not return_mapping:
            return [] if not uids else [None] * len(uids)
        elif not consider_relationships:
            return ([], dict()) if not uids else ([None] * len(uids), dict())

        if uids:
            return self._get_by_uids(uids, consider_relationships,
                                     return_mapping=return_mapping)
        return self._get_by_cuba_key(cuba_key, consider_relationships,
                                     return_mapping=return_mapping)

    def _get_by_uids(self, uids, relationships, return_mapping):
        """Check for each given uid if it is connected to self by a relationship.
        If not, replace it with None.
        Optionally return a mapping from uids to the set of relationships,
        which connect self and the cuds_object with the uid.

        :param uids: The uids to check.
        :type uids: List[UUID]
        :param relationships: Only consider these relationships
        :type relationships: List[Relationship]
        :param return_mapping: whether to return a mapping from
            uids to relationships, that connect self with the uid.
        :type return_mapping: bool
        :return: list of found uids, None for not found UUIDs
            (+ Mapping from UUIDs to relationships, which connect self to the
            respective Cuds object.)
        :rtype: List[UUID] (+ Dict[UUID, Set[Relationship]])
        """
        not_found_uids = dict(enumerate(uids)) if uids else None
        relationship_mapping = dict()
        for relationship in relationships:

            # Uids are given.
            # Check which occur as object of current relation.
            found_uid_indexes = set()

            # we need to iterate over all uids for every
            # relationship if we compute a mapping
            iterator = enumerate(uids) if relationship_mapping \
                else not_found_uids.items()
            for i, uid in iterator:
                if uid in self[relationship]:
                    found_uid_indexes.add(i)
                    if uid not in relationship_mapping:
                        relationship_mapping[uid] = set()
                    relationship_mapping[uid].add(relationship)
            for i in found_uid_indexes:
                if i in not_found_uids:
                    del not_found_uids[i]

        collected_uids = [(uid if i not in not_found_uids else None)
                          for i, uid in enumerate(uids)]
        if return_mapping:
            return collected_uids, relationship_mapping
        return collected_uids

    def _get_by_cuba_key(self, cuba_key, relationships, return_mapping):
        """Get the cuds_objects with given cuba_key that are connected to self
        with any of the given relationships. Optionally return a mapping
        from uids to the set of relationships, which connect self and
        the cuds_objects with the uid.

        :param cuba_key: Filter by the given cuba_key. None means no filter.
        :type cuba_key: CUBA
        :param relationships: Filter by list of relationships
        :type relationships: List[Relationship]
        :param return_mapping: whether to return a mapping from
            uids to relationships, that connect self with the uid.
        :type return_mapping: bool
        :return: The uids of the found Cuds
            (+ Mapping from uuid to set of
            relationsships that connect self with the respective cuds_object.)
        :rtype: List[UUID] (+ Dict[UUID, Set[Relationship]])
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        relationship_mapping = dict()
        for relationship in relationships:

            # Collect all uids who are object of the current relationship.
            # Possibly filter by Cuba-Key.
            for uid, cuba in self[relationship].items():
                if cuba_key is None or issubclass(CUBA_MAPPING[cuba],
                                                  CUBA_MAPPING[cuba_key]):
                    if uid not in relationship_mapping:
                        relationship_mapping[uid] = set()
                    relationship_mapping[uid].add(relationship)
        if return_mapping:
            return list(relationship_mapping.keys()), relationship_mapping
        return list(relationship_mapping.keys())

    def _load_cuds_objects(self, uids):
        """Load the cuds_objects of the given uids from the session.
        Each in cuds_object is at the same position in the result as
        the corresponding uid in the given uid list.
        If the given uids contain None values, there will be
        None values at the same postion in the result.

        :param uids: The uids to fetch from the session.
        :type uids: List[UUID]
        :return: The loaded cuds_objects
        :rtype: Iterator[Cuds]
        """
        without_none = [uid for uid in uids if uid is not None]
        cuds_objects = self.session.load(*without_none)
        for uid in uids:
            if uid is None:
                yield None
            else:
                try:
                    yield next(cuds_objects)
                except StopIteration:
                    return None

    def _remove_direct(self, relationship, uid):
        """Remove the direct relationship between self and
        the object with the given uid.

        :param relationship: The relationship to remove.
        :type relationship: Type[Relationship]
        :param uid: The uid to remove.
        :type uid: UUID
        """
        del self[relationship][uid]
        if not self[relationship]:
            del self[relationship]

    def _remove_inverse(self, relationship, uid):
        """Remove the inverse of the given relationship.

        :param relationship: The relationship to remove.
        :type relationship: Type[Relationship]
        :param uid: The uid to remove.
        :type uid: UUID
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        inverse = CUBA_MAPPING[relationship.inverse]
        self._remove_direct(inverse, uid)


class NotifyDict(dict):
    """A dictionary that notifies the session if
    any update occurs. Used to map uids to cuba_keys
    for each relationship.
    """
    def __init__(self, *args, cuds_object, rel):
        self.cuds_object = cuds_object
        self.rel = rel
        super().__init__(*args)

    def __iter__(self):
        self.cuds_object.session._notify_read(self)
        return super().__iter__()

    def __getitem__(self, key):
        self.cuds_object.session._notify_read(self)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self.cuds_object._check_valid_add(value, self.rel)
        self.cuds_object.session._notify_read(self.cuds_object)
        super().__setitem__(key, value)
        self.cuds_object.session._notify_update(self.cuds_object)

    def __delitem__(self, key):
        self.cuds_object.session._notify_read(self.cuds_object)
        super().__delitem__(key)
        self.cuds_object.session._notify_update(self.cuds_object)

    def update(self, E):
        self.cuds_object.session._notify_read(self.cuds_object)
        super().update(E)
        self.cuds_object.session._notify_update(self.cuds_object)
