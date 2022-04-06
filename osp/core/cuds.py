"""A Common Universal Data Structure.

The CUDS object is an ontology individual that can be used like a container. It
has attributes and is connected to other cuds objects via relationships.
"""

import logging
from copy import deepcopy
from typing import (
    Any,
    Dict,
    Hashable,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)
from uuid import UUID, uuid4

import rdflib
from rdflib import RDF, BNode, Graph, Literal, URIRef

import osp.core.warnings as warning_settings
from osp.core.namespaces import cuba, from_iri
from osp.core.neighbor_dict import NeighborDictRel
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.datatypes import CUDS_IRI_PREFIX
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.session.core_session import core_session
from osp.core.session.session import Session
from osp.core.utils.wrapper_development import (
    check_arguments,
    clone_cuds_object,
    create_from_cuds_object,
    get_neighbor_diff,
)

logger = logging.getLogger("osp.core")

CUDS_NAMESPACE_IRI = URIRef(CUDS_IRI_PREFIX)


class Cuds:
    """A Common Universal Data Structure.

    The CUDS object is an ontology individual that can be used like a
    container. It has attributes and is connected to other cuds objects via
    relationships.
    """

    _session = core_session

    def __init__(
        self,
        # Create from oclass and attributes dict.
        attributes: Dict[OntologyAttribute, Any],
        oclass: Optional[OntologyClass] = None,
        session: Session = None,
        iri: URIRef = None,
        uid: Union[UUID, URIRef] = None,
        # Specify extra triples for the CUDS object.
        extra_triples: Iterable[
            Tuple[
                Union[URIRef, BNode],
                Union[URIRef, BNode],
                Union[URIRef, BNode],
            ]
        ] = tuple(),
    ):
        """Initialize a CUDS object."""
        # Set uid. This is a "user-facing" method, so strict types
        # checks are performed.
        if len(set(filter(lambda x: x is not None, (uid, iri)))) > 1:
            raise ValueError(
                "Tried to initialize a CUDS object specifying, "
                "both its IRI and UID. A CUDS object is "
                "constrained to have just one UID."
            )
        elif uid is not None and type(uid) not in (UUID, URIRef):
            raise ValueError(
                "Provide either a UUID or a URIRef object" "as UID."
            )
        elif iri is not None and type(iri) is not URIRef:
            raise ValueError("Provide a URIRef object as IRI.")
        else:
            self._uid = uid or iri or uuid4()

        # Create CUDS triples in internal temporary graph.
        self._graph = Graph()
        if attributes:
            for k, v in attributes.items():
                self._graph.add(
                    (
                        self.iri,
                        k.iri,
                        Literal(k.convert_to_datatype(v), datatype=k.datatype),
                    )
                )
        if oclass:
            self._graph.add((self.iri, RDF.type, oclass.iri))
        extra_oclass = False
        for s, p, o in extra_triples:
            if s != self.iri:
                raise ValueError(
                    "Trying to add extra triples to a CUDS "
                    "object with a subject that does not match "
                    "the CUDS object's IRI."
                )
            elif p == RDF.type:
                extra_oclass = True
            self._graph.add((s, p, o))
        oclass_assigned = bool(oclass) or extra_oclass
        if not oclass_assigned:
            raise TypeError(
                f"No oclass associated with {self}! "
                f"Did you install the required ontology?"
            )

        self._session = session or Cuds._session
        # Copy temporary graph to the session graph and discard it.
        self.session._store(self)

    @property
    def iri(self) -> URIRef:
        """Get the IRI of the CUDS object."""
        return (
            self.uid
            if type(self.uid) is URIRef
            else URIRef(CUDS_NAMESPACE_IRI + str(self.uid))
        )

    @property
    def uid(self) -> Union[URIRef, UUID]:
        """Get the uid of the CUDS object.

        This is the public getter of the property.
        """
        return self._uid

    @property
    def _uid(self) -> Union[URIRef, UUID]:
        """Get the uid of the CUDS object.

        This is the private getter of the property.
        """
        return self.__uid

    @_uid.setter
    def _uid(self, value: Union[URIRef, UUID, int]):
        """Set the uid of a CUDS object.

        This is the private setter of the property.
        """
        if type(value) is int:
            value = UUID(int=value)
        if type(value) is UUID:
            invalid = value.int == 0
        else:
            split = value.split(":")
            invalid = not len(split) > 1 or any(x == "" for x in split)
        if invalid:
            raise ValueError(f"Invalid uid: {value}.")
        self.__uid = value

    @property
    def session(self) -> Session:
        """Get the session of the cuds object."""
        return self._session

    @property
    def oclasses(self):
        """Get the ontology classes of this CUDS object."""
        result = list()
        for o in self._graph.objects(self.iri, RDF.type):
            r = from_iri(o, raise_error=False)
            if r is not None:
                result.append(r)
        return result

    @property
    def oclass(self):
        """Get the type of the cuds object."""
        oclasses = self.oclasses
        if oclasses:
            return oclasses[0]
        return None

    @property
    def _neighbors(self):
        return NeighborDictRel(self)

    @property
    def _stored(self):
        return self.session is not None and self._graph is self.session.graph

    def get_triples(self, include_neighbor_types=False):
        """Get the triples of the cuds object."""
        o_set = set()
        for s, p, o in self._graph.triples((self.iri, None, None)):
            yield s, p, o
            o_set.add(o)
        if include_neighbor_types:
            for o in o_set:
                yield from self._graph.triples((o, RDF.type, None))

    def get_attributes(self):
        """Get the attributes as a dictionary."""
        if self.session:
            self.session._notify_read(self)
        result = {}
        for s, p, o in self._graph.triples((self.iri, None, None)):
            obj = from_iri(p, raise_error=False)
            if isinstance(obj, OntologyAttribute):
                value = self._rdflib_5_inplace_modification_prevention_filter(
                    o.toPython(), obj
                )
                result[obj] = value
        return result

    def is_a(self, oclass):
        """Check if the CUDS object is an instance of the given oclass.

        Args:
            oclass (OntologyClass): Check if the CUDS object is an instance of
                this oclass.

        Returns:
            bool: Whether the CUDS object is an instance of the given oclass.
        """
        return any(oc in oclass.subclasses for oc in self.oclasses)

    def add(
        self, *args: "Cuds", rel: OntologyRelationship = None
    ) -> Union["Cuds", List["Cuds"]]:
        """Add CUDS objects to their respective relationship.

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
        rel = rel or self.oclass.namespace.get_default_rel()
        if rel is None:
            raise TypeError(
                "Missing argument 'rel'! No default "
                "relationship specified for namespace %s."
                % self.oclass.namespace
            )
        result = list()
        # update cuds objects if they are already in the session
        old_objects = self._session.load(
            *[arg.uid for arg in args if arg.session != self.session]
        )
        for arg in args:
            # Recursively add the children to the registry
            if rel in self._neighbors and arg.uid in self._neighbors[rel]:
                message = "{!r} is already in the container"
                raise ValueError(message.format(arg))
            if self.session != arg.session:
                arg = self._recursive_store(arg, next(old_objects))

            self._add_direct(arg, rel)
            arg._add_inverse(self, rel)
            result.append(arg)
        return result[0] if len(args) == 1 else result

    def get(
        self,
        *uids: Union[UUID, URIRef],
        rel: OntologyRelationship = cuba.activeRelationship,
        oclass: OntologyClass = None,
        return_rel: bool = False,
    ) -> Union["Cuds", List["Cuds"]]:
        """Return the contained elements.

        Filter elements by given type, uid or relationship.
        Expected calls are get(), get(*uids), get(rel), get(oclass),
        get(*indentifiers, rel), get(rel, oclass).
        If uids are specified:
            The position of each element in the result is determined by to the
            position of the corresponding uid in the given list of
            uids. In this case, the result can contain None values if a
            given uid is not a child of this cuds_object.
            If only a single indentifier is given, only this one element is
            returned (i.e. no list).
        If no uids are specified:
            The result is a collection, where the elements are ordered
            randomly.

        Args:
            uids (Union[UUID, URIRef]): uids of the elements.
            rel (OntologyRelationship, optional): Only return cuds_object
                which are connected by subclass of given relationship.
                Defaults to cuba.activeRelationship.
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
        """Update the Cuds object.

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
            message = "Cannot update because cuds_object not added."
            raise ValueError(message)

        result = list()
        for arg, old_cuds_object in zip(args, old_objects):
            if arg.session is self.session:
                raise ValueError(
                    "Please provide CUDS objects from a "
                    "different session to update()"
                )
            # Updates all instances
            result.append(self._recursive_store(arg, old_cuds_object))

        if len(args) == 1:
            return result[0]
        return result

    def remove(
        self,
        *args: Union["Cuds", UUID, URIRef],
        rel: OntologyRelationship = cuba.activeRelationship,
        oclass: OntologyClass = None,
    ):
        """Remove elements from the CUDS object.

        Expected calls are remove(), remove(*uids/Cuds),
        remove(rel), remove(oclass), remove(*uids/Cuds, rel),
        remove(rel, oclass)

        Args:
            args (Union[Cuds, UUID, URIRef]): UUIDs of the elements to remove
                or the elements themselves.
            rel (OntologyRelationship, optional): Only remove cuds_object
                which are connected by subclass of given relationship.
                Defaults to cuba.activeRelationship.
            oclass (OntologyClass, optional): Only remove elements which are a
                subclass of the given ontology class. Defaults to None.

        Raises:
            RuntimeError: No CUDS object removed, because specified CUDS
                objects are not in the container of the current CUDS object
                directly.
        """
        uids = [arg.uid if isinstance(arg, Cuds) else arg for arg in args]

        # Get mapping from uids to connecting relationships
        _, relationship_mapping = self._get(
            *uids, rel=rel, oclass=oclass, return_mapping=True
        )
        if not relationship_mapping:
            raise RuntimeError(
                "Did not remove any Cuds object, "
                "because none matched your filter."
            )
        uid_relationships = list(relationship_mapping.items())

        # load all the neighbors to delete and remove inverse relationship
        neighbors = self.session.load(*[uid for uid, _ in uid_relationships])
        for uid_relationship, neighbor in zip(uid_relationships, neighbors):
            uid, relationships = uid_relationship
            for relationship in relationships:
                self._remove_direct(relationship, uid)
                neighbor._remove_inverse(relationship, self.uid)

    def iter(
        self,
        *uids: Union[UUID, URIRef],
        rel: OntologyRelationship = cuba.activeRelationship,
        oclass: OntologyClass = None,
        return_rel: bool = False,
    ) -> Iterator["Cuds"]:
        """Iterate over the contained elements.

        Only iterate over objects of a given type, uid or oclass.

        Expected calls are iter(), iter(*uids), iter(rel),
        iter(oclass), iter(*uids, rel), iter(rel, oclass).
        If uids are specified:
            The position of each element in the result is determined by to the
            position of the corresponding uid in the given list of
            uids. In this case, the result can contain None values if a
            given uid is not a child of this cuds_object.
        If no uids are specified:
            The result is ordered randomly.

        Args:
            uids (Union[UUID, URIRef]): uids of the elements.
            rel (OntologyRelationship, optional): Only return cuds_object
                which are connected by subclass of given relationship.
                Defaults to cuba.activeRelationship.
            oclass (OntologyClass, optional): Only return elements which are a
                subclass of the given ontology class. Defaults to None.
            return_rel (bool, optional): Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Iterator[Cuds]: The queried objects.
        """
        if return_rel:
            collected_uids, mapping = self._get(
                *uids, rel=rel, oclass=oclass, return_mapping=True
            )
        else:
            collected_uids = self._get(*uids, rel=rel, oclass=oclass)

        result = self._load_cuds_objects(collected_uids)
        for r in result:
            if not return_rel:
                yield r
            else:
                yield from ((r, m) for m in mapping[r.uid])

    def _recursive_store(self, new_cuds_object, old_cuds_object=None):
        """Recursively store cuds_object and all its children.

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
            new_cuds_object = create_from_cuds_object(
                new_cuds_object, add_to.session
            )
            # fix the connections to the neighbors
            add_to._fix_neighbors(
                new_cuds_object, old_cuds_object, add_to.session, missing
            )
            result = result or new_cuds_object

            for outgoing_rel in new_cuds_object._neighbors:

                # do not recursively add parents
                if not outgoing_rel.is_subclass_of(cuba.activeRelationship):
                    continue

                # add children not already added
                for child_uid in new_cuds_object._neighbors[outgoing_rel]:
                    if child_uid not in uids_stored:
                        new_child = new_child_getter.get(
                            child_uid, rel=outgoing_rel
                        )
                        old_child = self.session.load(child_uid).first()
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
        """Fix all the connections of the neighbors of a Cuds object.

        That CUDS is going to be replaced later.

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
            new_cuds_object, old_cuds_object, mode="non-active"
        )
        # get the neighbors that were neighbors
        # before adding the new cuds_object
        old_neighbor_diff = get_neighbor_diff(old_cuds_object, new_cuds_object)

        # Load all the cuds_objects of the session
        cuds_objects = iter(
            session.load(
                *[uid for uid, _ in new_parent_diff + old_neighbor_diff]
            )
        )

        # Perform the fixes
        Cuds._fix_new_parents(
            new_cuds_object=new_cuds_object,
            new_parents=cuds_objects,
            new_parent_diff=new_parent_diff,
            missing=missing,
        )
        Cuds._fix_old_neighbors(
            new_cuds_object=new_cuds_object,
            old_cuds_object=old_cuds_object,
            old_neighbors=cuds_objects,
            old_neighbor_diff=old_neighbor_diff,
        )

    @staticmethod
    def _fix_new_parents(
        new_cuds_object,
        new_parents,
        new_parent_diff: List[
            Tuple[Union[UUID, URIRef], OntologyRelationship]
        ],
        missing,
    ):
        """Fix the relationships of the added Cuds objects.

        Fixes relationships to the parents of the added Cuds object.

        Args:
            new_cuds_object (Cuds): The added Cuds object.
            new_parents (Iterator[Cuds]): The new parents of the added CUDS
                object.
            new_parent_diff : stuff.
                The uids of the new parents and the relations they are
                connected with.
            missing (dict): dictionary that will be populated with connections
                to objects, that are currently not available in the new
                session. The recursive_add might add it later.
        """
        # Iterate over the new parents
        for (parent_uid, relationship), parent in zip(
            new_parent_diff, new_parents
        ):
            if relationship.is_subclass_of(cuba.activeRelationship):
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
                parent._neighbors[inverse] = {}

            parent._neighbors[inverse][
                new_cuds_object.uid
            ] = new_cuds_object.oclasses

    @staticmethod
    def _fix_old_neighbors(
        new_cuds_object,
        old_cuds_object,
        old_neighbors: List[Tuple[Union[UUID, URIRef], OntologyRelationship]],
        old_neighbor_diff,
    ):
        """Fix the relationships of the added Cuds objects.

        Fixes relationships to Cuds object that were previously neighbors.

        Args:
            new_cuds_object (Cuds): The added Cuds object
            old_cuds_object (Cuds, optional): The Cuds object that is going
                to be replaced
            old_neighbors (Iterator[Cuds]): The Cuds object that were neighbors
                before the replacement.
            old_neighbor_diff: The uids of the old neighbors and the
                relations they are connected with.
        """
        # iterate over all old neighbors.
        for (neighbor_uid, relationship), neighbor in zip(
            old_neighbor_diff, old_neighbors
        ):
            inverse = relationship.inverse

            # delete the inverse if neighbors are children
            if relationship.is_subclass_of(cuba.activeRelationship):
                if inverse in neighbor._neighbors:
                    neighbor._remove_direct(inverse, new_cuds_object.uid)

            # if neighbor is parent, add missing relationships
            else:
                if relationship not in new_cuds_object._neighbors:
                    new_cuds_object._neighbors[relationship] = {}
                for (uid, oclasses), parent in zip(
                    old_cuds_object._neighbors[relationship].items(),
                    neighbor._neighbors,
                ):
                    if parent is not None:
                        new_cuds_object._neighbors[relationship][
                            uid
                        ] = oclasses

    def _add_direct(self, cuds_object, rel):
        """Add an cuds_object with a specific relationship.

        Args:
            cuds_object (Cuds): CUDS object to be added
            rel (OntologyRelationship): relationship with the cuds_object to
                add.
        """
        # First element, create set
        if rel not in self._neighbors:
            self._neighbors[rel] = dict()
        self._neighbors[rel][cuds_object.uid] = cuds_object.oclasses

    def _add_inverse(self, cuds_object, rel):
        """Add the inverse relationship from self to cuds_object.

        Args:
            cuds_object (Cuds): CUDS object to connect with.
            rel (OntologyRelationship): direct relationship
        """
        inverse_rel = rel.inverse
        self._add_direct(cuds_object, inverse_rel)

    def _get(self, *uids, rel=None, oclass=None, return_mapping=False):
        """Get the uid of contained elements that satisfy the filter.

        This filter consists of a certain type, uid or relationship.
        Expected calls are _get(), _get(*uids), _get(rel),_ get(oclass),
        _get(*uids, rel), _get(rel, oclass).
        If uids are specified, the result is the input, but
        non-available uids are replaced by None.

        Args:
            uids (Union[UUID, URIRef]): uids of the elements to
                get.
            rel (OntologyRelationship, optional): Only return CUDS objects
                connected with a subclass of relationship. Defaults to None.
            oclass (OntologyClass, optional): Only return CUDS objects of a
                subclass of this ontology class. Defaults to None.
            return_mapping (bool, optional): Whether to return a mapping from
                uids to relationships, that connect self with the
                uid. Defaults to False.

        Raises:
            TypeError: Specified both uids and oclass.
            ValueError: Wrong type of argument.

        Returns:
            List[Union[UUID, URIRef]] (+ Dict[Union[UUID, URIRef],
            Set[Relationship]]): list of uids, or None, if not found.
                (+ Mapping from UUIDs to relationships, which connect self to
                the respective Cuds object.)
        """
        if uids and oclass is not None:
            raise TypeError("Do not specify both uids and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise ValueError(
                "Found object of type %s passed to argument rel. "
                "Should be an OntologyRelationship." % type(rel)
            )
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise ValueError(
                "Found object of type %s passed to argument "
                "oclass. Should be an OntologyClass." % type(oclass)
            )

        if uids:
            check_arguments((UUID, URIRef), *uids)

        self.session._notify_read(self)
        # consider either given relationship and subclasses
        # or all relationships.
        consider_relationships = set(self._neighbors)
        if rel:
            consider_relationships &= set(rel.subclasses)
        consider_relationships = list(consider_relationships)

        # return empty list if no element of given relationship is available.
        if not consider_relationships and not return_mapping:
            return [] if not uids else [None] * len(uids)
        elif not consider_relationships:
            return ([], dict()) if not uids else ([None] * len(uids), dict())

        if uids:
            return self._get_by_uids(
                uids, consider_relationships, return_mapping=return_mapping
            )
        return self._get_by_oclass(
            oclass, consider_relationships, return_mapping=return_mapping
        )

    def _get_by_uids(self, uids, relationships, return_mapping):
        """Check for each given uid if it is connected by a given relationship.

        If not, replace it with None.
        Optionally return a mapping from uids to the set of
        relationships, which connect self and the cuds_object with the
        uid.

        Args:
            uids (List[Union[UUID, URIRef]]): The uids to check.
            relationships (List[Relationship]): Only consider these
                relationships.
            return_mapping (bool): Whether to return a mapping from
                uids to relationships, that connect self with the
                uid.

        Returns:
            List[Union[UUID, URIRef]] (+ Dict[Union[UUID, URIRef],
            Set[Relationship]]): list of found uids, None for not found
                uids (+ Mapping from uids to relationships, which
                connect self to the respective Cuds object.)
        """
        collected_uid = [None] * len(uids)
        relationship_mapping = dict()
        uids_cache = {
            relationship: set(self._neighbors[relationship])
            for relationship in relationships
        }
        for i, uid in enumerate(uids):
            relationship_set = {
                relationship
                for relationship in relationships
                if uid in uids_cache[relationship]
            }
            # The following line was a performance hog, and was therefore
            #  replaced by the one above.
            #                   if uid in self._neighbors[relationship]}
            if relationship_set:
                collected_uid[i] = uid
                relationship_mapping[uid] = relationship_set

        return (
            collected_uid
            if not return_mapping
            else (collected_uid, relationship_mapping)
        )

    def _get_by_oclass(self, oclass, relationships, return_mapping):
        """Get the cuds_objects with given oclass.

        Only return objects that are connected to self
        with any of the given relationships. Optionally return a mapping
        from uids to the set of relationships, which connect self and
        the cuds_objects with the uid.

        Args:
            oclass (OntologyClass, optional): Filter by the given
                OntologyClass. None means no filter.
            relationships (List[Relationship]): Filter by list of
                relationships.
            return_mapping (bool): whether to return a mapping from uids
            to relationships, that connect self with the uid.

        Returns:
            List[Union[UUID, URIRef]] (+ Dict[Union[UUID, URIRef],
            Set[Relationship]]): The uids of the found CUDS objects
                (+ Mapping from uid to set of relationsships that
                connect self with the respective cuds_object.)
        """
        relationship_mapping = dict()
        for relationship in relationships:

            # Collect all uids who are object of the current
            # relationship. Possibly filter by OntologyClass.
            for uid, target_classes in self._neighbors[relationship].items():
                if oclass is None or any(
                    t.is_subclass_of(oclass) for t in target_classes
                ):
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
        None values at the same position in the result.

        Args:
            uids (List[Union[UUID, URIRef]]): The uids to fetch
            from the session.

        Yields:
            Cuds: The loaded cuds_objects
        """
        without_none = filter(None, uids)
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
        """Remove the direct relationship to the object with given uid.

        Args:
            relationship (OntologyRelationship): The relationship to remove.
            uid (Union[UUID, URIRef]): The uid to remove.
        """
        del self._neighbors[relationship][uid]
        if not self._neighbors[relationship]:
            del self._neighbors[relationship]

    def _remove_inverse(self, relationship, uid):
        """Remove the inverse of the given relationship.

        Args:
            relationship (OntologyRelationship): The relationship to remove.
            uid (Union[UUID, URIRef]): The uid to remove.
        """
        inverse = relationship.inverse
        self._remove_direct(inverse, uid)

    def _check_valid_add(self, to_add, rel):
        return True  # TODO

    def __str__(self) -> str:
        """Get a human readable string.

        Returns:
            str: string with the Ontology class and uid.
        """
        return "%s: %s" % (self.oclass, self.uid)

    def __getattr__(self, name):
        """Set the attributes corresponding to ontology values.

        Args:
            name (str): The name of the attribute

        Raises:
            AttributeError: Unknown attribute name

        Returns:
            The value of the attribute: Any
        """
        try:
            identifier = self._get_attribute_identifier_by_argname(name)
            if self.session:
                self.session._notify_read(self)
            value = self._rdflib_5_inplace_modification_prevention_filter(
                self._graph.value(self.iri, identifier).toPython(), identifier
            )
            return value
        except AttributeError as e:
            if (  # check if user calls session's methods on wrapper
                self.is_a(cuba.Wrapper)
                and self._session is not None
                and hasattr(self._session, name)
            ):
                logger.warning(
                    "Trying to get non-defined attribute '%s' "
                    "of wrapper CUDS object '%s'. Will return attribute of "
                    "its session '%s' instead." % (name, self, self._session)
                )
                return getattr(self._session, name)
            raise AttributeError(name) from e

    def _get_attribute_by_argname(self, name):
        """Get the attributes of this CUDS by argname."""
        for oclass in self.oclasses:
            attr = oclass.get_attribute_by_argname(name)
            if attr is not None:
                return attr
        raise AttributeError(name)

    def _get_attribute_identifier_by_argname(self, name):
        """Get the identifier of an attribute of this CUDS by argname."""
        for oclass in self.oclasses:
            identifier = oclass.get_attribute_identifier_by_argname(name)
            if identifier is not None:
                return identifier
        raise AttributeError(name)

    @staticmethod
    def _rdflib_5_inplace_modification_prevention_filter(
        value: Any, attribute: OntologyAttribute
    ) -> Any:
        if rdflib.__version__ < "6.0.0" and not isinstance(value, Hashable):
            value = deepcopy(value)
            if warning_settings.attributes_cannot_modify_in_place:
                warning_settings.attributes_cannot_modify_in_place = False
                logger.warning(
                    f"Attribute {attribute} references the mutable "
                    f"object {value} of type {type(value)}. Please "
                    f"note that because you have `rdflib < 6.0.0` "
                    f"installed, if you modify this object "
                    f"in-place, the changes will not be reflected "
                    f"on the cuds object's attribute. \n"
                    f"For example, executing "
                    f"`fr = city.City(name='Freiburg', "
                    f"coordinates=[1, 2]); fr.coordinates[0]=98; "
                    f"fr.coordinates` would yield `array([1, 2])` "
                    f"instead of `array([98, 2])`, as you could "
                    f"expect. Use `fr.coordinates = [98, 2]` "
                    f"instead, or save the attribute to a "
                    f"different variable, i.e. `value = "
                    f"fr.coordinates; value[0] = 98, "
                    f"fr.coordinates = value`."
                    f"\n"
                    f"You will not see this kind of warning again "
                    f"during this session. You can turn off the "
                    f"warning by running `import osp.core.warnings "
                    f"as warning_settings; warning_settings."
                    f"attributes_cannot_modify_in_place = False`."
                )
        return value

    def __setattr__(self, name, new_value):
        """Set an attribute.

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
        attr = self._get_attribute_by_argname(name)
        if self.session:
            self.session._notify_read(self)
        self._graph.set(
            (
                self.iri,
                attr.iri,
                Literal(
                    attr.convert_to_datatype(new_value), datatype=attr.datatype
                ),
            )
        )
        if self.session:
            self.session._notify_update(self)

    def __repr__(self) -> str:
        """Return a machine readable string that represents the cuds object.

        Returns:
            str: Machine readable string representation for Cuds.
        """
        return "<%s: %s,  %s: @%s>" % (
            self.oclass,
            self.uid,
            type(self.session).__name__,
            hex(id(self.session)),
        )

    def __hash__(self) -> int:
        """Make Cuds objects hashable.

        Use the hash of the uid of the object

        Returns:
            int: unique hash
        """
        return hash(self.uid)

    def __eq__(self, other):
        """Define which CUDS objects are treated as equal.

        Same Ontology class and same uid.

        Args:
            other (Cuds): Instance to check.

        Returns:
            bool: True if they share the uid and class, False otherwise
        """
        return (
            isinstance(other, Cuds)
            and other.oclass == self.oclass
            and self.uid == other.uid
        )

    def __getstate__(self):
        """Get the state for pickling or copying.

        Returns:
            Dict[str, Any]: The state of the object. Does not contain session.
                Contains the string of the OntologyClass.
        """
        state = {
            k: v
            for k, v in self.__dict__.items()
            if k not in {"_session", "_graph"}
        }
        state["_graph"] = list(self.get_triples(include_neighbor_types=True))
        return state

    def __setstate__(self, state):
        """Set the state for pickling or copying.

        Args:
            state (Dict[str, Any]): The state of the object. Does not contain
                session. Contains the string of the OntologyClass.
        """
        state["_session"] = None
        g = Graph()
        for triple in state["_graph"]:
            g.add(triple)
        state["_graph"] = g
        self.__dict__ = state
