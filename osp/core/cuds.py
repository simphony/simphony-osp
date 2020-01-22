# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

# from __future__ import annotations
import uuid
from typing import Union, List, Iterator, Dict, Any

from osp.core import ONTOLOGY_INSTALLER
from osp.core.ontology.relationship import OntologyEntity
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.datatypes import convert_to
from osp.core.session.core_session import CoreSession
from osp.core.session.session import Session
from osp.core.neighbour_dict import NeighbourDictRel, NeighbourDictTarget
from osp.core.utils import check_arguments, clone_cuds_object, \
    create_from_cuds_object, get_neighbour_diff
from osp.core import CUBA


class Cuds():
    """
    A Common Universal Data Structure

    The cuds object has attributes and is connected to other
    cuds objects via relationships.
    """
    _session = CoreSession()

    def __init__(
        self,
        attributes: Dict[OntologyAttribute, Any],
        oclass: OntologyEntity,
        session: Session = None,
        uid: uuid.UUID = None
    ):
        """
        Initialization follows the behavior of the python dict class.

        :param uid: Specify a unique identifier. If None given, a random
            uid will be created.
        :type uid: UUID
        """
        self._attr_values = {k.argname: k(v) for k, v in attributes.items()}
        self._neighbours = NeighbourDictRel({}, self)

        self.__uid = uuid.uuid4() if uid is None else convert_to(uid, "UUID")
        self._session = session or Cuds._session
        self._onto_attributes = {k.argname: k for k in attributes}
        self._oclass = oclass
        self.session._store(self)

    @property
    def uid(self) -> uuid.UUID:
        """The uid of the cuds object"""
        return self.__uid

    @property
    def session(self):
        """The session of the cuds object"""
        return self._session

    @property
    def oclass(self):
        """The type of the cuds object"""
        return self._oclass

    def is_a(self, oclass):
        """Check if self is an instance of the given oclass.

        :param oclass: Check if self is an instance of this oclass.
        :type oclass: OntologyClass
        :return: Whether self is an instance of the given oclass.
        :rtype: bool
        """
        return self.oclass in oclass.subclasses

    def add(self,
            *args: "Cuds",
            rel: OntologyRelationship = None) -> Union["Cuds", List["Cuds"]]:
        """
        Adds (a) cuds(s) to their respective relationship.
        Before adding, check for invalid keys to avoid inconsistencies later.

        :param args: object(s) to add
        :type args: Cuds
        :param rel: class of the relationship between the objects
        :type rel: OntologyRelationship
        :return: The added object(s)
        :rtype: Union[Cuds, List[Cuds]]
        :raises ValueError: adding an element already there
        """
        check_arguments(Cuds, *args)
        rel = rel or self.oclass.namespace.default_rel
        if rel is None:
            raise TypeError("Missing argument 'rel'! No default "
                            "relationship specified for namespace %s."
                            % self.oclass.namespace)
        result = list()
        # update cuds objects if they are already in the session
        old_objects = self._session.load(
            *[arg.uid for arg in args if arg.session != self.session])
        for arg in args:
            # Recursively add the children to the registry
            if rel in self._neighbours and arg.uid in self._neighbours[rel]:
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
            rel: OntologyRelationship = CUBA.ACTIVE_RELATIONSHIP,
            oclass: OntologyClass = None) -> Union["Cuds", List["Cuds"]]:
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(oclass),
        get(*uids, rel), get(rel, oclass).
        If uids are specified, the position of each element in the result
        is determined by to the position of the corresponding uid in the given
        list of uids.
        In this case, the result can contain None values if a given uid is not
        a child of this cuds_object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements
        :param rel: Only return cuds_object which are connected by subclass of
            given relationship.
        :type rel: OntologyRelationship
        :param oclass: Type (Ontology class) of the subelements
        :type oclass: OntologyClass
        :return: the queried objects, or None, if not found
        :rtype: Union[Cuds, List[Cuds]]
        """
        collected_uids = self._get(*uids, rel=rel, oclass=oclass)
        result = list(self._load_cuds_objects(collected_uids))
        if len(uids) == 1:
            return result[0]
        return result

    def update(self, *args: "Cuds") -> List["Cuds"]:
        """
        Updates the object with the other versions.

        :param args: updated cuds objects
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
            if arg.session is self.session:
                raise ValueError("Please provide CUDS objects from a "
                                 "different session to update()")
            # Updates all instances
            result.append(self._recursive_store(arg, old_cuds_object))

        if len(args) == 1:
            return result[0]
        return result

    def remove(self,
               *args: Union["Cuds", uuid.UUID],
               rel: OntologyRelationship = CUBA.ACTIVE_RELATIONSHIP,
               oclass: OntologyClass = None):
        """
        Removes elements from the Cuds.
        Expected calls are remove(), remove(*uids/Cuds),
        remove(rel), remove(oclass), remove(*uids/Cuds, rel),
        remove(rel, oclass)

        :param args: UIDs of the elements or the elements themselves
        :type args: Union[Cuds, UUID]
        :param rel: Only remove cuds_object which are connected by subclass of
            given relationship
        :type rel: OntologyRelationship
        :param oclass: Type (Ontology Class) of the subelements
        :type oclass: OntologyClass
        """
        uids = [arg.uid if isinstance(arg, Cuds) else arg for arg in args]

        # Get mapping from uids to connecting relationships
        _, relationship_mapping = self._get(*uids, rel=rel, oclass=oclass,
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
             rel: OntologyRelationship = CUBA.ACTIVE_RELATIONSHIP,
             oclass: OntologyClass = None) -> Iterator["Cuds"]:
        """
        Iterates over the contained elements of a certain type, uid or
        relationship. Expected calls are iter(), iter(*uids), iter(rel),
        iter(oclass), iter(*uids, rel), iter(rel, oclass).
        If uids are specified, the each element will be yielded in the order
        given by list of uids.
        In this case, elements can be None values if a given uid is not
        a child of this cuds_object.
        If no uids are specified, the resulting elements are ordered randomly.

        :param uids: UIDs of the elements.
        :type uids: UUID
        :param rel: class of the relationship.
        :type rel: OntologyRelationship
        :param oclass: Type of the subelements.
        :type oclass: OntologyClass
        :return: Iterator over of queried objects, or None, if not found.
        :rtype: Iterator[Cuds]
        """
        collected_uids = self._get(*uids, rel=rel, oclass=oclass)
        yield from self._load_cuds_objects(collected_uids)

    def _str_attributes(self):
        """
        Serializes the relevant attributes from the instance.

        :return: list with the attributes in a key-value form string
        """
        attributes = []
        for attribute in sorted(self.get_values(skip=["session"])):
            attributes.append(attribute + ": " + str(getattr(self, attribute)))

        return attributes

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

            for outgoing_rel in new_cuds_object._neighbours:

                # do not recursively add parents
                if not outgoing_rel.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP):
                    continue

                # add children not already added
                for child_uid in new_cuds_object._neighbours[outgoing_rel]:
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
                del cuds_object._neighbours[rel][uid]
                if not cuds_object._neighbours[rel]:
                    del cuds_object._neighbours[rel]
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
        old_cuds_object = old_cuds_object or None

        # get the parents that got parents after adding the new Cuds
        new_parent_diff = get_neighbour_diff(
            new_cuds_object, old_cuds_object, mode="non-active")
        # get the neighbours that were neighbours
        # before adding the new cuds_object
        old_neighbour_diff = get_neighbour_diff(old_cuds_object,
                                                new_cuds_object)

        # Load all the cuds_objects of the session
        cuds_objects = iter(session.load(
            *[uid for uid, _ in new_parent_diff + old_neighbour_diff]))

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
        # Iterate over the new parents
        for (parent_uid, relationship), parent in zip(new_parent_diff,
                                                      new_parents):
            if relationship.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP):
                continue
            inverse = relationship.inverse
            # Delete connection to parent if parent is not present
            if parent is None:
                if parent_uid not in missing:
                    missing[parent_uid] = list()
                missing[parent_uid].append((new_cuds_object, relationship))
                continue

            # Add the inverse to the parent
            if inverse not in parent._neighbours:
                parent._neighbours[inverse] = NeighbourDictTarget({}, parent,
                                                                  inverse)

            parent._neighbours[inverse][new_cuds_object.uid] = \
                new_cuds_object.oclass

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
        # iterate over all old neighbours.
        for (neighbour_uid, relationship), neighbour in zip(old_neighbour_diff,
                                                            old_neighbours):
            inverse = relationship.inverse

            # delete the inverse if neighbours are children
            if relationship.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP):
                if inverse in neighbour._neighbours:
                    neighbour._remove_direct(inverse, new_cuds_object.uid)

            # if neighbour is parent, add missing relationships
            else:
                if relationship not in new_cuds_object._neighbours:
                    new_cuds_object._neighbours[relationship] = \
                        NeighbourDictTarget({}, new_cuds_object, relationship)
                for (uid, oclass), parent in \
                        zip(old_cuds_object._neighbours[relationship].items(),
                            neighbour._neighbours):
                    if parent is not None:
                        new_cuds_object._neighbours[relationship][uid] = oclass

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
        if rel not in self._neighbours.keys():
            self._neighbours[rel] = NeighbourDictTarget(
                {cuds_object.uid: cuds_object.oclass},
                self, rel
            )
        # Element not already there
        elif cuds_object.uid not in self._neighbours[rel]:
            self._neighbours[rel][cuds_object.uid] = cuds_object.oclass

    def _add_inverse(self, cuds_object, rel):
        """
        Adds the inverse relationship from self to cuds_object.

        :param cuds_object: container of the normal relationship
        :param rel: direct relationship instance
        """
        inverse_rel = rel.inverse
        self._add_direct(cuds_object, inverse_rel)

    def _get(self, *uids, rel=None, oclass=None, return_mapping=False):
        """
        Returns the uid of contained elements of a certain type, uid or
        relationship.
        Expected calls are _get(), _get(*uids), _get(rel),_ get(oclass),
        _get(*uids, rel), _get(rel, oclass).
        If uids are specified, the result is the input, but
        non-available uids are replaced by None.

        :param uids: UIDs of the elements
        :type uids
        :param rel: class of the relationship, optional
        :type rel: OntologyRelationship
        :param oclass: Type subelements, optional
        :type oclass: OntologyClass
        :param return_mapping: whether to return a mapping from
            uids to relationships, that connect self with the uid.
        :type return_mapping: bool
        :return: list of uids, or None, if not found.
            (+ Mapping from UUIDs to relationships, which connect self to the
            respective Cuds object.)
        :rtype: List[UUID] (+ Dict[UUID, Set[Relationship]])
        """
        if uids and oclass is not None:
            raise TypeError("Do not specify both uids and oclass")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise ValueError("Found object of type %s passed to argument rel. "
                             "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise ValueError("Found object of type %s passed to argument "
                             "oclass. Should be an OntologyClass."
                             % type(oclass))

        if uids:
            check_arguments(uuid.UUID, *uids)

        self.session._notify_read(self)
        # consider either given relationship and subclasses
        # or all relationships.
        consider_relationships = set(self._neighbours.keys())
        if rel:
            consider_relationships &= set(rel.subclasses)
        consider_relationships = list(consider_relationships)

        # return empty list if no element of given relationship is available.
        if not consider_relationships and not return_mapping:
            return [] if not uids else [None] * len(uids)
        elif not consider_relationships:
            return ([], dict()) if not uids else ([None] * len(uids), dict())

        if uids:
            return self._get_by_uids(uids, consider_relationships,
                                     return_mapping=return_mapping)
        return self._get_by_oclass(oclass, consider_relationships,
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
                if uid in self._neighbours[relationship]:
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

    def _get_by_oclass(self, oclass, relationships, return_mapping):
        """Get the cuds_objects with given oclass that are connected to self
        with any of the given relationships. Optionally return a mapping
        from uids to the set of relationships, which connect self and
        the cuds_objects with the uid.

        :param oclass: Filter by the given OntologyClass. None means no filter.
        :type oclass: OntologyClass
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
        relationship_mapping = dict()
        for relationship in relationships:

            # Collect all uids who are object of the current relationship.
            # Possibly filter by OntologyClass.
            for uid, target_class in self._neighbours[relationship].items():
                if oclass is None or target_class.is_subclass_of(oclass):
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
        :type relationship: OntologyRelationship
        :param uid: The uid to remove.
        :type uid: UUID
        """
        del self._neighbours[relationship][uid]
        if not self._neighbours[relationship]:
            del self._neighbours[relationship]

    def _remove_inverse(self, relationship, uid):
        """Remove the inverse of the given relationship.

        :param relationship: The relationship to remove.
        :type relationship: OntologyRelationship
        :param uid: The uid to remove.
        :type uid: UUID
        """
        inverse = relationship.inverse
        self._remove_direct(inverse, uid)

    def _check_valid_add(self, to_add, rel):
        return True  # TODO

    def __str__(self) -> str:
        """
        Redefines the str() for Cuds.

        :return: string with the Ontology class and uid.
        """
        return "%s: %s" % (self.oclass, self.uid)

    def __getattr__(self, name):
        """Set the attributes corresponding to ontology values

        :param name: The name of the attribute
        :type name: str
        :raises AttributeError: Unknown attribute name
        :return: The value of the attribute
        :rtype: Any
        """
        if name not in self._attr_values:
            raise AttributeError(name)
        if self.session:
            self.session._notify_read(self)
        if name not in self._attr_values:
            raise AttributeError(name)
        return self._attr_values[name]

    def __setattr__(self, name, new_value):
        """Set an attribute.
            Will notify the session of it corresponds to an ontology value.

        :param name: The name of the attribute.
        :type name: str
        :param new_value: The new value
        :type new_value: Any
        :raises AttributeError: Unknown attribute name
        """
        if name.startswith("_"):
            super().__setattr__(name, new_value)
            return
        if name not in self._attr_values:
            raise AttributeError(name)
        if self.session:
            self.session._notify_read(self)
        if name not in self._attr_values:
            raise AttributeError(name)
        self._attr_values[name] = self._onto_attributes[name](new_value)
        if self.session:
            self.session._notify_update(self)

    def __repr__(self) -> str:
        """
        Redefines the repr() for Cuds.

        :return: string with the official string representation for Cuds.
        """
        return "<%s: %s,  %s: @%s>" % (self.oclass, self.uid,
                                       type(self.session).__name__,
                                       hex(id(self.session)))

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
        return other.oclass == self.oclass and self.uid == other.uid

    def __getstate__(self):
        """Get the state for pickling or copying

        :return: The state of the object. Does not contain session.
            Contains the string of the OntologyClass.
        :rtype: Dict[str, Any]
        """
        state = {k: v for k, v in self.__dict__.items()
                 if k not in {"_session", "_oclass", "_values"}}
        state["_oclass"] = (self.oclass.namespace.name, self._oclass.name)
        state["_neighbours"] = [
            (k.namespace.name, k.name, [
                (uid, vv.namespace.name, vv.name)
                for uid, vv in v.items()
            ])
            for k, v in self._neighbours.items()
        ]
        state["_values"] = [(k, v.namespace.name, v.name)
                            for k, v in self._onto_attributes.items()]
        return state

    def __setstate__(self, state):
        """Set the state for pickling or copying

        :param state: The state of the object. Does not contain session.
            Contains the string of the OntologyClass.
        :type state: Dict[str, Any]
        """
        namespace, oclass = state["_oclass"]
        oclass = ONTOLOGY_INSTALLER.namespace_registry[namespace][oclass]
        state["_oclass"] = oclass
        state["_session"] = None
        state["_neighbours"] = NeighbourDictRel({
            ONTOLOGY_INSTALLER.namespace_registry[ns][cl]:
                NeighbourDictTarget({
                    uid: ONTOLOGY_INSTALLER.namespace_registry[ns2][cl2]
                    for uid, ns2, cl2 in v
                }, self, ONTOLOGY_INSTALLER.namespace_registry[ns][cl])
            for ns, cl, v in state["_neighbours"]
        }, self)
        state["_values"] = {k: ONTOLOGY_INSTALLER.namespace_registry[ns][cl]
                            for k, ns, cl in state["_values"]}
        self.__dict__ = state
