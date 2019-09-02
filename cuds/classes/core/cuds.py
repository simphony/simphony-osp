# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

# from __future__ import annotations
import uuid
import inspect
from typing import Union, Type, List, Iterator, Dict, Any

from cuds.metatools.ontology_datatypes import convert_to
from cuds.classes.core.session.core_session import CoreSession
from cuds.classes.core.relationship_tree import RelationshipTree
from cuds.utils import check_arguments
from cuds.classes.generated.relationship import Relationship
from cuds.classes.generated.cuba import CUBA
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
    supported_relationships = dict()
    session = CoreSession()
    CUDS_SETTINGS = {
        'check_relationship_supported': False,
        'check_cardinalities': True
    }

    def __init__(self, uid: uuid.UUID = None):
        """
        Initialization follows the behavior of the python dict class.

        :param uid: Specify a unique identifier. If none, given a random
            uid will be created.
        :type uid: UUID
        """
        super().__init__()
        from cuds.classes.generated import CUDS_SETTINGS
        Cuds.CUDS_SETTINGS.update(CUDS_SETTINGS)
        self.__uid = uuid.uuid4() if uid is None else convert_to(uid, "UUID")
        # store the hierarchical order of the relationships
        self._relationship_tree = RelationshipTree(self.ROOT_REL)
        self.session.store(self)

    @property
    def uid(self) -> uuid.UUID:
        return self.__uid

    def __str__(self) -> str:
        """
        Redefines the str() for Cuds.

        :return: string with the cuba_key and uid.
        """
        return "%s: %s" % (self.cuba_key, self.uid)

    def __delitem__(self, key: Type[Relationship]):
        """Delete a relationship from the Cuds.

        :param key: The relationship to remove
        :type key: Type[Relationship]
        :raises ValueError: The given key is not a relationship.
        """
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
        if inspect.isclass(key) and issubclass(key, self.ROOT_REL) \
                and isinstance(value, dict):
            for _, entity_cuba in value.items():
                self._check_valid_add(entity_cuba, key)
            # Any changes to the dict should be sent to the session
            super().__setitem__(key, NotifyDict(value, cuds=self, rel=key))
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
        """Get all the attributes of the cuds object.

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
        """Get the datatypes of the attributes of the cuds object.

        :return: The datatypes of the attributes as a mapping
            from attribute to datatype
        :rtype: Dict[str, str]
        """
        return inspect.getfullargspec(cls.__init__).annotations

    def add(self,
            *args: "Cuds",
            rel: Type[Relationship] = None) -> Union["Cuds", List["Cuds"]]:
        """
        Adds (a) cuds object(s) to their respective CUBA key relationship.
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
        for arg in args:
            if arg.session != self.session:
                arg = arg._clone()
            self._add_direct(arg, rel)
            arg._add_inverse(self, rel)
            result.append(arg)

            # Recursively add the children to the registry
            if self.session != arg.session:
                result[-1] = self._recursive_store(arg)
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
        a child of this cuds object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements
        :param rel: Only return cuds which are connected by subclass of
            given relationship.
        :type rel: Type[Relationship]
        :param cuba_key: CUBA key of the subelements
        :type cuba_key: CUBA
        :return: the queried objects, or None, if not found
        :rtype: Union[Cuds, List[Cuds]]
        """
        collected_uids = self._get(*uids, rel=rel, cuba_key=cuba_key)
        result = list(self._load_entities(collected_uids))
        if len(uids) == 1:
            return result[0]
        return result

    def update(self, *args: "Cuds") -> List["Cuds"]:
        """
        Updates the object with the other versions.

        :param args: updated entity(ies)
        :type args: Cuds
        :return: The updated cuds.
        :rtype: Union[Cuds, List[Cuds]]
        """
        check_arguments(Cuds, *args)
        old_objects = self.get(*[arg.uid for arg in args])
        if len(args) == 1:
            old_objects = [old_objects]
        if any(x is None for x in old_objects):
            message = 'Cannot update because entity not added.'
            raise ValueError(message)

        result = list()
        for arg, old_cuds in zip(args, old_objects):
            # Updates all instances
            result.append(self._recursive_store(arg, old_cuds))

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
        :param rel: Only remove cuds which are connected by subclass of
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

        # load all the neighbors to delete and remove inverse relationship, too
        neighbors = self.session.load(*[uid for uid, _ in uid_relationships])
        for uid_relationship, neighbor in zip(uid_relationships, neighbors):
            uid, relationships = uid_relationship
            for relationship in relationships:
                self._remove_direct(relationship, uid)
                neighbor._remove_inverse(relationship, self.uid)

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
        a child of this cuds object.
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
        yield from self._load_entities(collected_uids)

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

    def _recursive_store(self, new_cuds, old_cuds=None):
        """Recursively store cuds and all its children.
        One-way relationships and dangling references are fixed.

        :param new_cuds: The Cuds object to store recursively.
        :type new_cuds: Cuds
        :param old_cuds: The old version of the cuds object, defaults to None
        :type old_cuds: Cuds, optional
        :rtype: Set[UUID]
        """
        # add new_cuds to self and replace old_cuds
        queue = [(self, new_cuds, old_cuds)]
        uids_stored = {new_cuds.uid}
        missing = dict()
        result = None
        while queue:

            # Store copy in registry
            add_to, new_cuds, old_cuds = queue.pop(0)
            if new_cuds.uid in missing:
                del missing[new_cuds.uid]
            new_child_getter = new_cuds
            new_cuds = new_cuds._clone()
            new_cuds.session = add_to.session
            # fix the connections to the neighbors
            add_to._fix_neighbors(new_cuds, old_cuds, add_to.session, missing)
            add_to.session.store(new_cuds)
            result = result if result is not None else new_cuds

            for outgoing_rel in new_cuds.keys():

                # do not recursively add parents
                if not issubclass(outgoing_rel, ActiveRelationship):
                    continue

                # add children not already added
                for child_uid in new_cuds[outgoing_rel].keys():
                    if child_uid not in uids_stored:
                        new_child = new_child_getter.get(
                            child_uid, rel=outgoing_rel)
                        old_child = old_cuds.get(child_uid,
                                                 rel=outgoing_rel) \
                            if old_cuds else None
                        queue.append((new_cuds, new_child, old_child))
                        uids_stored.add(new_child.uid)

        # perform the deletion
        for uid in missing:
            for cuds, rel in missing[uid]:
                del cuds[rel][uid]
                if not cuds[rel]:
                    del cuds[rel]
        return result

    @staticmethod
    def _fix_neighbors(new_cuds, old_cuds, session, missing):
        """Fix all the connections of the neighbors of a Cuds objects
        that is going to be replaced.

        Behavior when neighbors change:

        - new_cuds has parents, that weren't parents of old_cuds.
            - the parents are already stored in the session of old_cuds.
            - they are not already stored in the session of old_cuds.
            --> Add references between new_cuds and the parents that are
                already in the session.
            --> Delete references between new_cuds and parents that are
                not available.
        - new_cuds has children, that weren't children of old_cuds.
            --> add/update them recursively.

        - A parent of old_cuds is no longer a parent of new_cuds.
        --> Add a relationship between that parent and the new cuds.
        - A child of old_cuds is no longer a child of new_cuds.
        --> Remove the relationship between child and new_cuds.

        :param new_cuds: Cuds object that will replace the old one
        :type new_cuds: Cuds
        :param old_cuds: Cuds object that will be replaced by a new one.
            Can be None if the new Cuds object does not replace any object.
        :type old_cuds: Cuds
        :param session: The session where the adjustments should take place.
        :type session: Session
        :param missing: dictionary that will be populated with connections
            to objects, that are currently not available in the new session.
            The recursive add might add it later.
        :type missing: dict
        """
        old_cuds = old_cuds or dict()

        # get the parents that got parents after adding the new Cuds
        new_parent_diff = Cuds._get_neighbor_diff(
            new_cuds, old_cuds, rel=PassiveRelationship)
        # get the neighbors that were neighbors before adding the new cuds
        old_neighbor_diff = Cuds._get_neighbor_diff(old_cuds, new_cuds)

        # Load all the entities of the session
        entities = session.load(
            *[uid for uid, _ in new_parent_diff + old_neighbor_diff])

        # Perform the fixes
        Cuds._fix_new_parents(new_cuds=new_cuds,
                              new_parents=entities,
                              new_parent_diff=new_parent_diff,
                              missing=missing)
        Cuds._fix_old_neighbors(new_cuds=new_cuds,
                                old_cuds=old_cuds,
                                old_neighbors=entities,
                                old_neighbor_diff=old_neighbor_diff)

    @staticmethod
    def _fix_new_parents(new_cuds, new_parents, new_parent_diff, missing):
        """Fix the relationships beetween the added Cuds objects and
        the parents of the added Cuds object.
        # TODO test

        :param new_cuds: The added Cuds object
        :type new_cuds: Cuds
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
            if not issubclass(relationship, PassiveRelationship):
                continue
            inverse = CUBA_MAPPING[relationship.inverse]
            # Delete connection to parent if parent is not present
            if parent is None:
                if parent_uid not in missing:
                    missing[parent_uid] = list()
                missing[parent_uid].append((new_cuds, relationship))
                continue

            # Add the inverse to the parent
            if inverse not in parent:
                parent[inverse] = dict()

            parent[inverse][new_cuds.uid] = new_cuds.cuba_key

    @staticmethod
    def _fix_old_neighbors(new_cuds, old_cuds, old_neighbors,
                           old_neighbor_diff):
        """Fix the relationships beetween the added Cuds objects and
        the Cuds object that were previously neighbors.
        # TODO test

        :param new_cuds: The added Cuds object
        :type new_cuds: Cuds
        :param old_cuds: The Cuds object that is going to be replaced
        :type old_cuds: Union[Cuds, None]
        :param old_neighbors: The Cuds object that were neighbors before the
            replacement.
        :type old_neighbors: Iterator[Cuds]
        :param old_neighbor_diff: The uids of the old neigbors and the
            relations they are connected with
        :type old_neighbor_diff: List[Tuple[UID, Relationship]]
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING

        # iterate over all old neighbors.
        for (neighbor_uid, relationship), neighbor in zip(old_neighbor_diff,
                                                          old_neighbors):
            inverse = CUBA_MAPPING[relationship.inverse]

            # delete the inverse if neighbors are children
            if issubclass(relationship, ActiveRelationship):
                if inverse in neighbor:
                    neighbor._remove_direct(inverse, new_cuds.uid)

            # if neighbor is parent, add missing relationships
            else:
                if relationship not in new_cuds:
                    new_cuds[relationship] = dict()
                for (uid, cuba_key), parent in \
                        zip(old_cuds[relationship].items(), neighbor):
                    if parent is not None:
                        new_cuds[relationship][uid] = cuba_key

    @staticmethod
    def _get_neighbor_diff(cuds1, cuds2, rel=None):
        """Get the uids of neighbors of cuds1 which are no neighbors in cuds2.
        Furthermore get the relationship the neighbors are connected with.
        Optionally filter the considered relationships.
        # TODO test

        :param cuds1: A Cuds object.
        :type cuds1: Cuds
        :param cuds2: A Cuds object.
        :type cuds2: Cuds
        :param rel: Only consider rel and its subclasses, defaults to None
        :type rel: Relationship, optional
        :return: List of Tuples that contain the found uids and relationships.
        :rtype: List[Tuple[UUID, Relationship]]
        """

        result = list()
        # Iterate over all neighbors that are in cuds1 but not cuds2.
        for relationship in cuds1.keys():
            if rel is not None and not issubclass(relationship, rel):
                continue

            # Get all the neighbors that are no neighbors is cuds2
            old_neighbor_uids = set()
            if relationship in cuds2:
                old_neighbor_uids = cuds2[relationship].keys()
            new_neighbor_uids = list(
                cuds1[relationship].keys() - old_neighbor_uids)
            result += list(zip(new_neighbor_uids,
                               [relationship] * len(new_neighbor_uids)))
        return result

    def _add_direct(self, entity, rel, error_if_already_there=True):
        """
        Adds an entity to the current instance with a specific relationship
        :param entity: object to be added
        :type entity: Cuds
        :param rel: relationship with the entity to add
        :type rel: Type[Relationships]
        :param error_if_already_there: Whether to throw an error if the
            object to add has already been added previously.
        :type error_if_already_there: bool
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

    def _check_valid_add(self, entity_cuba, rel):
        """Check if adding should be allowed.

        :param entity: The entity to add.
        :type entity: Cuds
        :param rel: Relationship with the entity to add.
        :type rel: Relationship
        :raises ValueError: Add is illegal.
        """
        if not Cuds.CUDS_SETTINGS["check_relationship_supported"]:
            return

        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        for supported_relationships, supported_entities in \
                self.supported_relationships.items():
            if issubclass(rel, CUBA_MAPPING[supported_relationships]):
                for supported_entity in supported_entities:
                    if issubclass(CUBA_MAPPING[entity_cuba],
                                  CUBA_MAPPING[supported_entity]):
                        return

        raise ValueError(
            ("Cannot add %s to %s with relationship %s: "
                + "Invalid relationship or object. Check the ontology!")
            % (entity_cuba, self, rel))

    def _add_inverse(self, entity, rel):
        """
        Adds the inverse relationship from self to entity.

        :param entity: container of the normal relationship
        :param rel: direct relationship instance
        """
        from ..generated.cuba_mapping import CUBA_MAPPING
        inverse_rel = CUBA_MAPPING[rel.inverse]
        self._add_direct(entity, inverse_rel, error_if_already_there=False)

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
        :typre return_mapping: bool
        :return: list of uids, or None, if not found.
            (+ Mapping from UUIDs to relationships, which connect self to the
            respective Cuds object.)
        :rtype: List[UUID] (+ Dict[UUID, Set[Relationship]])
        """
        if uids and cuba_key is not None:
            raise RuntimeError("Do not specify both uids and cuba_key")

        if uids:
            check_arguments(uuid.UUID, *uids)

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
        which connect self and the cuds object with the uid.

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
                if uid in self.__getitem__(relationship):
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
        """Get the cuds with given cuba_key that are connected to self
        with any of the given relationships. Optionally return a mapping
        from uids to the set of relationships, which connect self and
        the cuds object with the uid.

        :param cuba_key: Filter by the given cuba_key. None means no filter.
        :type cuba_key: CUBA
        :param relationships: Filter by list of relationships
        :type relationships: List[Relationship]
        :param return_mapping: whether to return a mapping from
            uids to relationships, that connect self with the uid.
        :type return_mapping: bool
        :return: The uids of the found Cuds
            (+ Mapping from uuid to set of
            relationsships that connect self with the respective cuds.)
        :rtype: List[UUID] (+ Dict[UUID, Set[Relationship]])
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
        if return_mapping:
            return list(relationship_mapping.keys()), relationship_mapping
        return list(relationship_mapping.keys())

    def _load_entities(self, uids):
        """Load the entities of the given uids from the session.
        Each in entity is at the same position in the result as
        the corresponding uid in the given uid list.
        If the given uids contain None values, there will be
        None values at the same postion in the result.

        :param uids: The uids to fetch from the session.
        :type uids: List[UUID]
        :return: The loaded entities
        :rtype: Iterator[Cuds]
        """
        without_none = [uid for uid in uids if uid is not None]
        entities = self.session.load(*without_none)
        for uid in uids:
            if uid is None:
                yield None
            else:
                yield next(entities)

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


class NotifyDict(dict):
    """A dictionary that notifies the session if
    any update occurs. Used to map uids to cuba_keys
    for each relationship.
    """
    def __init__(self, *args, cuds, rel):
        self.cuds = cuds
        self.rel = rel
        super().__init__(*args)

    def __setitem__(self, key, value):
        self.cuds._check_valid_add(value, self.rel)
        super().__setitem__(key, value)
        self.cuds.session._notify_update(self.cuds)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.cuds.session._notify_update(self.cuds)

    def update(self, E):
        super().update(E)
        self.cuds.session._notify_update(self.cuds)
