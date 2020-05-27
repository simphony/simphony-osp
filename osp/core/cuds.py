# from __future__ import annotations
import uuid
import rdflib
import logging

from typing import Union, List, Iterator, Dict, Any
from osp.core import ONTOLOGY_INSTALLER
from osp.core.ontology.relationship import OntologyEntity
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.datatypes import convert_to
from osp.core.session.core_session import CoreSession
from osp.core.session.session import Session
from osp.core.neighbor_dict import NeighborDictRel, NeighborDictTarget
from osp.core.utils import check_arguments, clone_cuds_object, \
    create_from_cuds_object, get_neighbor_diff
from osp.core import CUBA

logger = logging.getLogger("osp.core")


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
        This method should not be called by the user directly.
        Instead use the __call__ magic method of OntologyClass.
        Construct the CUDS object. This will also register the CUDS objects in
        the corresponding session.

        Args:
            attributes (Dict[OntologyAttribute, Any]): Mapping from ontology
                attribute to specified value.
            oclass (OntologyEntity): The ontology class of the CUDS object.
            session (Session, optional): The session associated with the CUDS,
                if None is given it will be associated with the CoreSession.
                Defaults to None.
            uid (uuid.UUID, optional): A unique identifier. If None given, a
                random uid will be created. Defaults to None.

        Raises:
            ValueError: Uid of zero is not allowed.
        """
        self._attr_values = {k.argname: k.convert_to_datatype(v)
                             for k, v in attributes.items()}
        self._neighbors = NeighborDictRel({}, self)

        self.__uid = uuid.uuid4() if uid is None else convert_to(uid, "UUID")
        if self.__uid.int == 0:
            raise ValueError("Invalid UUID")
        self._session = session or Cuds._session
        self._onto_attributes = {k.argname: k for k in attributes}
        self._oclass = oclass
        self.session._store(self)

    @property
    def uid(self) -> uuid.UUID:
        """The uid of the cuds object"""
        return self.__uid

    @property
    def iri(self):
        """Get the IRI of the CUDS object"""
        return self._iri_from_uid(self.uid)

    @property
    def session(self):
        """The session of the cuds object"""
        return self._session

    @property
    def oclass(self):
        """The type of the cuds object"""
        return self._oclass

    def get_triples(self):
        """ Get the triples of the cuds object."""
        return [
            (self.iri, relationship.iri, self._iri_from_uid(uid))
            for uid, relationships in self._get(return_mapping=True)[1].items()
            for relationship in relationships
        ] + [
            (self.iri, attribute.iri, rdflib.Literal(value))
            for attribute, value in self.get_attributes().items()
        ] + [
            (self.iri, rdflib.RDF.type, self.oclass.iri)
        ]

    def get_attributes(self):
        """Get the attributes as a dictionary"""
        result = {}
        for attribute in self.oclass.attributes:
            result[attribute] = getattr(self, attribute.argname)
        return result

    def is_a(self, oclass):
        """
        Check if the CUDS object is an instance of the given oclass.

        Args:
            oclass (OntologyClass): Check if the CUDS object is an instance of
                this oclass.

        Returns:
            bool: Whether the CUDS object is an instance of the given oclass.
        """
        return self.oclass in oclass.subclasses

    def add(self,
            *args: "Cuds",
            rel: OntologyRelationship = None) -> Union["Cuds", List["Cuds"]]:
        """
        Adds CUDS objects to their respective relationship.
        If the added objects are associated with the same session,
        only a link is created. Otherwise, the a deepcopy is made and added
        to the session of this Cuds object.
        Before adding, check for invalid keys to avoid inconsistencies later.

        Args:
            args (Cuds): The objects to be added
            rel (OntologyRelationship): The relationship between the objects.

        Raises:
            TypeError: Ne relationship given and no default specified.
            ValueError: Added a CUDS object that is already in the container.

        Returns:
            Union[Cuds, List[Cuds]]: The CUDS objects that have been added,
                associated with the session of the current CUDS object.
                Result type is a list, if more than one CUDS object is
                returned.
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
            if rel in self._neighbors and arg.uid in self._neighbors[rel]:
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
            oclass: OntologyClass = None,
            return_rel: bool = False) -> Union["Cuds", List["Cuds"]]:
        """
        Returns the contained elements of a certain type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(oclass),
        get(*uids, rel), get(rel, oclass).
        If uids are specified:
            The position of each element in the result is determined by to the
            position of the corresponding uid in the given list of uids.
            In this case, the result can contain None values if a given uid
            is not a child of this cuds_object.
            If only a single uid is given, only this one element is returned
            (i.e. no list).
        If no uids are specified:
            The result is a collection, where the elements are ordered
            randomly.

        Args:
            uids (uuid.UUID): UUIDs of the elements.
            rel (OntologyRelationship, optional): Only return cuds_object
                which are connected by subclass of given relationship.
                Defaults to CUBA.ACTIVE_RELATIONSHIP.
            oclass (OntologyClass, optional): Only return elements which are a
                subclass of the given ontology class. Defaults to None.
            return_rel (bool, optional): Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Union[Cuds, List[Cuds]]: The queried objects.
        """
        result = list(
            self.iter(*uids, rel=rel, oclass=oclass, return_rel=return_rel)
        )
        if len(uids) == 1:
            return result[0]
        return result

    def update(self, *args: "Cuds") -> List["Cuds"]:
        """
        Updates the object by providing updated versions of CUDS objects
        that are directly in the container of this CUDS object.
        The updated versions must be associated with a different session.

        Args:
            args (Cuds): The updated versions to use to update the current
                object.

        Raises:
            ValueError: Provided a CUDS objects is not in the container of the
                current CUDS
            ValueError: Provided CUDS object is associated with the same
                session as the current CUDS object. Therefore it is not an
                updated version.

        Returns:
            Union[Cuds, List[Cuds]]: The CUDS objects that have been updated,
                associated with the session of the current CUDS object.
                Result type is a list, if more than one CUDS object is
                returned.
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
        Removes elements from the CUDS object.
        Expected calls are remove(), remove(*uids/Cuds),
        remove(rel), remove(oclass), remove(*uids/Cuds, rel),
        remove(rel, oclass)

        Args:
            args (Union[Cuds, UUID]): UUIDs of the elements to remove or the
                elements themselves.
            rel (OntologyRelationship, optional): Only remove cuds_object
                which are connected by subclass of given relationship.
                Defaults to CUBA.ACTIVE_RELATIONSHIP.
            oclass (OntologyClass, optional): Only remove elements which are a
                subclass of the given ontology class. Defaults to None.

        Raises:
            RuntimeError: No CUDS object removed, because specified CUDS
                objects are not in the container of the current CUDS object
                directly.
        """
        uids = [arg.uid if isinstance(arg, Cuds) else arg for arg in args]

        # Get mapping from uids to connecting relationships
        _, relationship_mapping = self._get(*uids, rel=rel, oclass=oclass,
                                            return_mapping=True)
        if not relationship_mapping:
            raise RuntimeError("Did not remove any Cuds object, "
                               + "because none matched your filter.")
        uid_relationships = list(relationship_mapping.items())

        # load all the neighbors to delete and remove inverse relationship
        neighbors = self.session.load(*[uid for uid, _ in uid_relationships])
        for uid_relationship, neighbor in zip(uid_relationships, neighbors):
            uid, relationships = uid_relationship
            for relationship in relationships:
                self._remove_direct(relationship, uid)
                neighbor._remove_inverse(relationship, self.uid)

    def iter(self,
             *uids: uuid.UUID,
             rel: OntologyRelationship = CUBA.ACTIVE_RELATIONSHIP,
             oclass: OntologyClass = None,
             return_rel: bool = False) -> Iterator["Cuds"]:
        """
        Iterates over the contained elements of a certain type, uid or
        relationship. Expected calls are iter(), iter(*uids), iter(rel),
        iter(oclass), iter(*uids, rel), iter(rel, oclass).
        If uids are specified:
            The position of each element in the result is determined by to the
            position of the corresponding uid in the given list of uids.
            In this case, the result can contain None values if a given uid
            is not a child of this cuds_object.
        If no uids are specified:
            The result is ordered randomly.

        Args:
            uids (uuid.UUID): UUIDs of the elements.
            rel (OntologyRelationship, optional): Only return cuds_object
                which are connected by subclass of given relationship.
                Defaults to CUBA.ACTIVE_RELATIONSHIP.
            oclass (OntologyClass, optional): Only return elements which are a
                subclass of the given ontology class. Defaults to None.
            return_rel (bool, optional): Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Iterator[Cuds]: The queried objects.
        """
        if return_rel:
            collected_uids, mapping = self._get(*uids, rel=rel, oclass=oclass,
                                                return_mapping=True)
        else:
            collected_uids = self._get(*uids, rel=rel, oclass=oclass)

        result = self._load_cuds_objects(collected_uids)
        for r in result:
            if not return_rel:
                yield r
            else:
                yield from ((r, m) for m in mapping[r.uid])

    def _recursive_store(self, new_cuds_object, old_cuds_object=None):
        """
        Recursively store cuds_object and all its children.
        One-way relationships and dangling references are fixed.

        Args:
            new_cuds_object (Cuds): The Cuds object to store recursively.
            old_cuds_object (Cuds, optional): The old version of the
                CUDS object. Defaults to None.

        Returns:
            Cuds: The added CUDS object.
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
            # fix the connections to the neighbors
            add_to._fix_neighbors(new_cuds_object, old_cuds_object,
                                  add_to.session, missing)
            result = result or new_cuds_object

            for outgoing_rel in new_cuds_object._neighbors:

                # do not recursively add parents
                if not outgoing_rel.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP):
                    continue

                # add children not already added
                for child_uid in new_cuds_object._neighbors[outgoing_rel]:
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
                del cuds_object._neighbors[rel][uid]
                if not cuds_object._neighbors[rel]:
                    del cuds_object._neighbors[rel]
        return result

    @staticmethod
    def _fix_neighbors(new_cuds_object, old_cuds_object, session, missing):
        """
        Fix all the connections of the neighbors of a Cuds objects
        that is going to be replaced.

        Behavior when neighbors change:

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

        Args:
            new_cuds_object (Cuds): Cuds object that will replace the old one.
            old_cuds_object (Cuds, optional): Cuds object that will be
                replaced by a new one. Can be None if the new Cuds object does
                not replace any object.
            session (Session): The session where the adjustments should take
                place.
            missing (Dict): dictionary that will be populated with connections
              to objects, that are currently not available in the new session.
              The recursive add might add it later.
        """
        old_cuds_object = old_cuds_object or None

        # get the parents that got parents after adding the new Cuds
        new_parent_diff = get_neighbor_diff(
            new_cuds_object, old_cuds_object, mode="non-active")
        # get the neighbors that were neighbors
        # before adding the new cuds_object
        old_neighbor_diff = get_neighbor_diff(old_cuds_object,
                                              new_cuds_object)

        # Load all the cuds_objects of the session
        cuds_objects = iter(session.load(
            *[uid for uid, _ in new_parent_diff + old_neighbor_diff]))

        # Perform the fixes
        Cuds._fix_new_parents(new_cuds_object=new_cuds_object,
                              new_parents=cuds_objects,
                              new_parent_diff=new_parent_diff,
                              missing=missing)
        Cuds._fix_old_neighbors(new_cuds_object=new_cuds_object,
                                old_cuds_object=old_cuds_object,
                                old_neighbors=cuds_objects,
                                old_neighbor_diff=old_neighbor_diff)

    @staticmethod
    def _fix_new_parents(new_cuds_object, new_parents,
                         new_parent_diff, missing):
        """
        Fix the relationships beetween the added Cuds objects and
        the parents of the added Cuds object.

        Args:
            new_cuds_object (Cuds): The added Cuds object
            new_parents (Iterator[Cuds]): The new parents of the added CUDS
                object
            new_parent_diff (List[Tuple[UID, Relationship]]): The uids of the
                new parents and the relations they are connected with.
            missing (dict): dictionary that will be populated with connections
                to objects, that are currently not available in the new
                session. The recursive_add might add it later.
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
            if inverse not in parent._neighbors:
                parent._neighbors[inverse] = NeighborDictTarget({}, parent,
                                                                inverse)

            parent._neighbors[inverse][new_cuds_object.uid] = \
                new_cuds_object.oclass

    @staticmethod
    def _fix_old_neighbors(new_cuds_object, old_cuds_object, old_neighbors,
                           old_neighbor_diff):
        """
        Fix the relationships beetween the added Cuds objects and
        the Cuds object that were previously neighbors.

        Args:
            new_cuds_object (Cuds): The added Cuds object
            old_cuds_object (Cuds, optional): The Cuds object that is going
                to be replaced
            old_neighbors (Iterator[Cuds]): The Cuds object that were neighbors
                before the replacement.
            old_neighbor_diff (List[Tuple[UID, Relationship]]): The uids of
                the old neighbors and the relations they are connected with.
        """
        # iterate over all old neighbors.
        for (neighbor_uid, relationship), neighbor in zip(old_neighbor_diff,
                                                          old_neighbors):
            inverse = relationship.inverse

            # delete the inverse if neighbors are children
            if relationship.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP):
                if inverse in neighbor._neighbors:
                    neighbor._remove_direct(inverse, new_cuds_object.uid)

            # if neighbor is parent, add missing relationships
            else:
                if relationship not in new_cuds_object._neighbors:
                    new_cuds_object._neighbors[relationship] = \
                        NeighborDictTarget({}, new_cuds_object, relationship)
                for (uid, oclass), parent in \
                        zip(old_cuds_object._neighbors[relationship].items(),
                            neighbor._neighbors):
                    if parent is not None:
                        new_cuds_object._neighbors[relationship][uid] = oclass

    def _add_direct(self, cuds_object, rel):
        """
        Adds an cuds_object to the current instance
        with a specific relationship

        Args:
            cuds_object (Cuds): CUDS object to be added
            rel (OntologyRelationship): relationship with the cuds_object to
                add.
        """
        # First element, create set
        if rel not in self._neighbors.keys():
            self._neighbors[rel] = NeighborDictTarget(
                {cuds_object.uid: cuds_object.oclass},
                self, rel
            )
        # Element not already there
        elif cuds_object.uid not in self._neighbors[rel]:
            self._neighbors[rel][cuds_object.uid] = cuds_object.oclass

    def _add_inverse(self, cuds_object, rel):
        """
        Adds the inverse relationship from self to cuds_object.

        Args:
            cuds_object (Cuds): CUDS object to connect with.
            rel (OntologyRelationship): direct relationship
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

        Args:
            uids (UUID): UUIDs of the elements to get.
            rel (OntologyRelationship, optional): Only return CUDS objects
                connected with a subclass of relationship. Defaults to None.
            oclass (OntologyClass, optional): Only return CUDS objects of a
                subclass of this ontology class. Defaults to None.
            return_mapping (bool, optional): Whether to return a mapping from
                uids to relationships, that connect self with the uid.
                Defaults to False.

        Raises:
            TypeError: Specified both uids and oclass.
            ValueError: Wrong type of argument.

        Returns:
            List[UUID] (+ Dict[UUID, Set[Relationship]]): list of uids, or
                None, if not found. (+ Mapping from UUIDs to relationships,
                which connect self to the respective Cuds object.)
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
        consider_relationships = set(self._neighbors.keys())
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
        """
        Check for each given uid if it is connected to self by a relationship.
        If not, replace it with None.
        Optionally return a mapping from uids to the set of relationships,
        which connect self and the cuds_object with the uid.

        Args:
            uids (List[UUID]): The uids to check.
            relationships (List[Relationship]): Only consider these
                relationships.
            return_mapping (bool): Wether to return a mapping from
                uids to relationships, that connect self with the uid.
        Returns:
            List[UUID] (+ Dict[UUID, Set[Relationship]]): list of found uids,
                None for not found UUIDs (+ Mapping from UUIDs to
                relationships, which connect self to the respective Cuds
                object.)
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
                if uid in self._neighbors[relationship]:
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
        """
        Get the cuds_objects with given oclass that are connected to self
        with any of the given relationships. Optionally return a mapping
        from uids to the set of relationships, which connect self and
        the cuds_objects with the uid.

        Args:
            oclass (OntologyClass, optional): Filter by the given
                OntologyClass. None means no filter.
            relationships (List[Relationship]): Filter by list of
                relationships.
            return_mapping (bool): whether to return a mapping from
                uids to relationships, that connect self with the uid.

        Returns:
            List[UUID] (+ Dict[UUID, Set[Relationship]]): The uids of the found
                CUDS objects (+ Mapping from uuid to set of relationsships that
                connect self with the respective cuds_object.)
        """
        relationship_mapping = dict()
        for relationship in relationships:

            # Collect all uids who are object of the current relationship.
            # Possibly filter by OntologyClass.
            for uid, target_class in self._neighbors[relationship].items():
                if oclass is None or target_class.is_subclass_of(oclass):
                    if uid not in relationship_mapping:
                        relationship_mapping[uid] = set()
                    relationship_mapping[uid].add(relationship)
        if return_mapping:
            return list(relationship_mapping.keys()), relationship_mapping
        return list(relationship_mapping.keys())

    def _load_cuds_objects(self, uids):
        """
        Load the cuds_objects of the given uids from the session.
        Each in cuds_object is at the same position in the result as
        the corresponding uid in the given uid list.
        If the given uids contain None values, there will be
        None values at the same postion in the result.

        Args:
            uids (List[UUID]): The uids to fetch from the session.

        Yields:
            Cuds: The loaded cuds_objects
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
        """
        Remove the direct relationship between self and
        the object with the given uid.

        Args:
            relationship (OntologyRelationship): The relationship to remove.
            uid (UUID): The uid to remove.
        """
        del self._neighbors[relationship][uid]
        if not self._neighbors[relationship]:
            del self._neighbors[relationship]

    def _remove_inverse(self, relationship, uid):
        """Remove the inverse of the given relationship.

        Args:
            relationship (OntologyRelationship): The relationship to remove.
            uid (UUID): The uid to remove.
        """
        inverse = relationship.inverse
        self._remove_direct(inverse, uid)

    def _check_valid_add(self, to_add, rel):
        return True  # TODO

    def _iri_from_uid(self, uid):
        """Transform a UUID to an IRI.

        Args:
            uid (UUID): The UUID to trasnform.

        Returns:
            URIRef: The IRI of the CUDS object with the given UUID.
        """
        from osp.core import IRI_DOMAIN
        return rdflib.URIRef(IRI_DOMAIN + "/#%s" % uid)

    def __str__(self) -> str:
        """
        Get a human readable string.

        Returns:
            str: string with the Ontology class and uid.
        """
        return "%s: %s" % (self.oclass, self.uid)

    def __getattr__(self, name):
        """Set the attributes corresponding to ontology values

        Args:
            name (str): The name of the attribute

        Raises:
            AttributeError: Unknown attribute name

        Returns:
            The value of the attribute: Any
        """
        if name not in self._attr_values:
            if (  # check if user calls session's methods on wrapper
                self.is_a(CUBA.WRAPPER)
                and self._session is not None
                and hasattr(self._session, name)
            ):
                logger.warn(
                    "Trying to get non-defined attribute '%s' "
                    "of wrapper CUDS object '%s'. Will return attribute of "
                    "its session '%s' instead." % (name, self, self._session)
                )
                return getattr(self._session, name)
            else:
                raise AttributeError(name)
        if self.session:
            self.session._notify_read(self)
        if name not in self._attr_values:
            raise AttributeError(name)
        return self._attr_values[name]

    def __setattr__(self, name, new_value):
        """
        Set an attribute.
        Will notify the session of it corresponds to an ontology value.

        Args:
            name (str): The name of the attribute.
            new_value (Any): The new value.

        Raises:
            AttributeError: Unknown attribute name
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
        self._attr_values[name] = \
            self._onto_attributes[name].convert_to_datatype(new_value)
        if self.session:
            self.session._notify_update(self)

    def __repr__(self) -> str:
        """
        Return a machine readable string that represents the cuds object.

        Returns:
            str: Machine readable string representation for Cuds.
        """

        return "<%s: %s,  %s: @%s>" % (self.oclass, self.uid,
                                       type(self.session).__name__,
                                       hex(id(self.session)))

    def __hash__(self) -> int:
        """
        Makes Cuds objects hashable.
        Use the hash of the uid of the object

        Returns:
            int: unique hash
        """

        return hash(self.uid)

    def __eq__(self, other):
        """
        Define which CUDS objects are treated as equal:
        Same Ontology class and same UUID.

        Args:
            other (Cuds): Instance to check.

        Returns:
            bool: True if they share the uid and class, False otherwise
        """

        return other.oclass == self.oclass and self.uid == other.uid

    def __getstate__(self):
        """
        Get the state for pickling or copying

        Returns:
            Dict[str, Any]: The state of the object. Does not contain session.
                Contains the string of the OntologyClass.
        """

        state = {k: v for k, v in self.__dict__.items()
                 if k not in {"_session", "_oclass", "_values"}}
        state["_oclass"] = (self.oclass.namespace.name, self._oclass.name)
        state["_neighbors"] = [
            (k.namespace.name, k.name, [
                (uid, vv.namespace.name, vv.name)
                for uid, vv in v.items()
            ])
            for k, v in self._neighbors.items()
        ]
        state["_values"] = [(k, v.namespace.name, v.name)
                            for k, v in self._onto_attributes.items()]
        return state

    def __setstate__(self, state):
        """
        Set the state for pickling or copying.

        Args:
            state (Dict[str, Any]): The state of the object. Does not contain
                session. Contains the string of the OntologyClass.
        """

        namespace, oclass = state["_oclass"]
        oclass = ONTOLOGY_INSTALLER.namespace_registry[namespace][oclass]
        state["_oclass"] = oclass
        state["_session"] = None
        state["_neighbors"] = NeighborDictRel({
            ONTOLOGY_INSTALLER.namespace_registry[ns][cl]:
                NeighborDictTarget({
                    uid: ONTOLOGY_INSTALLER.namespace_registry[ns2][cl2]
                    for uid, ns2, cl2 in v
                }, self, ONTOLOGY_INSTALLER.namespace_registry[ns][cl])
            for ns, cl, v in state["_neighbors"]
        }, self)
        state["_values"] = {k: ONTOLOGY_INSTALLER.namespace_registry[ns][cl]
                            for k, ns, cl in state["_values"]}
        self.__dict__ = state
