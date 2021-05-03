"""A Common Universal Data Structure.

The CUDS object is an ontology individual that can be used like a container. It
has attributes and is connected to other cuds objects via relationships.
"""

import logging
from uuid import uuid4, UUID
from typing import Union, List, Iterator, Dict, Any, Optional
from rdflib import URIRef, RDF, Graph, Literal
from osp.core.namespaces import cuba, from_iri
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.datatypes import CUDS_IRI_PREFIX
from osp.core.session.core_session import CoreSession
from osp.core.session.session import Session
from osp.core.neighbor_dict import NeighborDictRel
from osp.core.utils import check_arguments, clone_cuds_object, \
    create_from_cuds_object, get_neighbor_diff

logger = logging.getLogger("osp.core")

CUDS_NAMESPACE_IRI = URIRef(CUDS_IRI_PREFIX)


class Cuds:
    """A Common Universal Data Structure.

    The CUDS object is an ontology individual that can be used like a
    container. It has attributes and is connected to other cuds objects via
    relationships.
    """

    _session = CoreSession()

    def __init__(self,
                 attributes: Dict[OntologyAttribute, Any],
                 oclass: Optional[OntologyClass] = None,
                 session: Session = None,
                 identifier: Union[UUID, URIRef] = None,
                 iri: URIRef = None,
                 uid: UUID = None):
        """Initialize a CUDS object."""
        # Set identifier.
        if identifier is not None and any(x is not None for x in (iri, uid)):
            raise Exception("The keyword argument `identifier` cannot be used"
                            "at the same time as the keyword arguments `iri`"
                            "or `uuid`.")
        elif all(x is not None for x in (iri, uid)):
            raise Exception("Tried to initialize a CUDS object specifying, "
                            "both its IRI and its UID. A CUDS object is "
                            "constrained to have just one identifier.")
        else:
            self._identifier = identifier or uid or iri or uuid4()

        # Create CUDS triples in internal temporary graph.
        self._graph = Graph()
        for k, v in attributes.items():
            self._graph.add((
                self.iri, k.iri, Literal(k.convert_to_datatype(v),
                                         datatype=k.datatype)
            ))
        if oclass:
            self._graph.add((
                self.iri, RDF.type, oclass.iri
            ))

        self._session = session or Cuds._session
        # Copy temporary graph to the session graph and discard it.
        self.session._store(self)

    @property
    def iri(self) -> URIRef:
        """Get the IRI of the CUDS object."""
        return self.identifier if type(self.identifier) is URIRef else \
            URIRef(CUDS_NAMESPACE_IRI + str(self.identifier))

    @property
    def identifier(self) -> Union[URIRef, UUID]:
        """Get the identifier of the CUDS object.

        This is the public getter of the property.
        """
        return self._identifier

    @property
    def _identifier(self) -> Union[URIRef, UUID]:
        """
        Get the identifier of the CUDS object.

        This is the private getter of the property
        """
        return self.__identifier

    @_identifier.setter
    def _identifier(self, value: Union[URIRef, UUID, int]):
        """Set the identifier of a CUDS object.

        This is the private setter of the property.
        """
        if type(value) is int:
            value = UUID(int=value)
        if type(value) is UUID:
            invalid = value.int == 0
        else:
            split = value.split(':')
            invalid = not len(split) > 1 or any(x == "" for x in split)
        if invalid:
            raise ValueError(f"Invalid identifier: {value}.")
        self.__identifier = value

    @property
    def session(self) -> Session:
        """Get the session of the cuds object."""
        return self._session

    @property
    def oclasses(self):
        """Get the ontology classes of this CUDS object."""
        result = list()
        for s, p, o in self._graph.triples((self.iri, RDF.type, None)):
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
                result[obj] = o.toPython()
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

    def add(self,
            *args: "Cuds",
            rel: OntologyRelationship = None) -> Union["Cuds", List["Cuds"]]:
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
            raise TypeError("Missing argument 'rel'! No default "
                            "relationship specified for namespace %s."
                            % self.oclass.namespace)
        result = list()
        # update cuds objects if they are already in the session
        old_objects = self._session.load(
            *[arg.identifier for arg in args if arg.session != self.session])
        for arg in args:
            # Recursively add the children to the registry
            if rel in self._neighbors \
                    and arg.identifier in self._neighbors[rel]:
                message = '{!r} is already in the container'
                raise ValueError(message.format(arg))
            if self.session != arg.session:
                arg = self._recursive_store(arg, next(old_objects))

            self._add_direct(arg, rel)
            arg._add_inverse(self, rel)
            result.append(arg)
        return result[0] if len(args) == 1 else result

    def get(self,
            *identifiers: Union[UUID, URIRef],
            rel: OntologyRelationship = cuba.activeRelationship,
            oclass: OntologyClass = None,
            return_rel: bool = False) -> Union["Cuds", List["Cuds"]]:
        """Return the contained elements.

        Filter elements by given type, identifier or relationship.
        Expected calls are get(), get(*identifiers), get(rel), get(oclass),
        get(*indentifiers, rel), get(rel, oclass).
        If identifiers are specified:
            The position of each element in the result is determined by to the
            position of the corresponding identifier in the given list of
            identifiers. In this case, the result can contain None values if a
            given identifier is not a child of this cuds_object.
            If only a single indentifier is given, only this one element is
            returned (i.e. no list).
        If no identifiers are specified:
            The result is a collection, where the elements are ordered
            randomly.

        Args:
            identifiers (Union[UUID, URIRef]): Identifiers of the elements.
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
            self.iter(*identifiers, rel=rel, oclass=oclass,
                      return_rel=return_rel)
        )
        if len(identifiers) == 1:
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
        old_objects = self.get(*[arg.identifier for arg in args])
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
               *args: Union["Cuds", UUID, URIRef],
               rel: OntologyRelationship = cuba.activeRelationship,
               oclass: OntologyClass = None):
        """Remove elements from the CUDS object.

        Expected calls are remove(), remove(*identifiers/Cuds),
        remove(rel), remove(oclass), remove(*identifiers/Cuds, rel),
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
        identifiers = [arg.identifier if isinstance(arg, Cuds) else
                       arg for arg in args]

        # Get mapping from identifiers to connecting relationships
        _, relationship_mapping = self._get(*identifiers, rel=rel,
                                            oclass=oclass, return_mapping=True)
        if not relationship_mapping:
            raise RuntimeError("Did not remove any Cuds object, "
                               "because none matched your filter.")
        identifier_relationships = list(relationship_mapping.items())

        # load all the neighbors to delete and remove inverse relationship
        neighbors = self.session.load(
            *[identifier for identifier, _ in identifier_relationships])
        for identifier_relationship, neighbor in zip(identifier_relationships,
                                                     neighbors):
            identifier, relationships = identifier_relationship
            for relationship in relationships:
                self._remove_direct(relationship, identifier)
                neighbor._remove_inverse(relationship, self.identifier)

    def iter(self,
             *identifiers: Union[UUID, URIRef],
             rel: OntologyRelationship = cuba.activeRelationship,
             oclass: OntologyClass = None,
             return_rel: bool = False) -> Iterator["Cuds"]:
        """Iterate over the contained elements.

        Only iterate over objects of a given type, identifier or oclass.

        Expected calls are iter(), iter(*identifiers), iter(rel),
        iter(oclass), iter(*identifiers, rel), iter(rel, oclass).
        If identifiers are specified:
            The position of each element in the result is determined by to the
            position of the corresponding identifier in the given list of
            identifiers. In this case, the result can contain None values if a
            given identifier is not a child of this cuds_object.
        If no identifiers are specified:
            The result is ordered randomly.

        Args:
            identifiers (Union[UUID, URIRef]): identifiers of the elements.
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
            collected_identifiers, mapping = self._get(*identifiers, rel=rel,
                                                       oclass=oclass,
                                                       return_mapping=True)
        else:
            collected_identifiers = self._get(*identifiers, rel=rel,
                                              oclass=oclass)

        result = self._load_cuds_objects(collected_identifiers)
        for r in result:
            if not return_rel:
                yield r
            else:
                yield from ((r, m) for m in mapping[r.identifier])

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
        identifiers_stored = {new_cuds_object.identifier, self.identifier}
        missing = dict()
        result = None
        while queue:

            # Store copy in registry
            add_to, new_cuds_object, old_cuds_object = queue.pop(0)
            if new_cuds_object.identifier in missing:
                del missing[new_cuds_object.identifier]
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
                if not outgoing_rel.is_subclass_of(cuba.activeRelationship):
                    continue

                # add children not already added
                for child_identifier in \
                        new_cuds_object._neighbors[outgoing_rel]:
                    if child_identifier not in identifiers_stored:
                        new_child = new_child_getter.get(
                            child_identifier, rel=outgoing_rel)
                        old_child = self.session.load(child_identifier).first()
                        queue.append((new_cuds_object, new_child, old_child))
                        identifiers_stored.add(new_child.identifier)

        # perform the deletion
        for identifier in missing:
            for cuds_object, rel in missing[identifier]:
                del cuds_object._neighbors[rel][identifier]
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
            new_cuds_object, old_cuds_object, mode="non-active")
        # get the neighbors that were neighbors
        # before adding the new cuds_object
        old_neighbor_diff = get_neighbor_diff(old_cuds_object,
                                              new_cuds_object)

        # Load all the cuds_objects of the session
        cuds_objects = iter(session.load(
            *[identifier for identifier, _ in
              new_parent_diff + old_neighbor_diff]))

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
        """Fix the relationships of the added Cuds objects.

        Fixes relationships to the parents of the added Cuds object.

        Args:
            new_cuds_object (Cuds): The added Cuds object
            new_parents (Iterator[Cuds]): The new parents of the added CUDS
                object
            new_parent_diff (List[Tuple[Union[UUID, URIRef], Relationship]]):
                The identifiers of the new parents and the relations they are
                connected with.
            missing (dict): dictionary that will be populated with connections
                to objects, that are currently not available in the new
                session. The recursive_add might add it later.
        """
        # Iterate over the new parents
        for (parent_identifier, relationship), parent in zip(new_parent_diff,
                                                             new_parents):
            if relationship.is_subclass_of(cuba.activeRelationship):
                continue
            inverse = relationship.inverse
            # Delete connection to parent if parent is not present
            if parent is None:
                if parent_identifier not in missing:
                    missing[parent_identifier] = list()
                missing[parent_identifier].append((new_cuds_object,
                                                   relationship))
                continue

            # Add the inverse to the parent
            if inverse not in parent._neighbors:
                parent._neighbors[inverse] = {}

            parent._neighbors[inverse][new_cuds_object.identifier] = \
                new_cuds_object.oclasses

    @staticmethod
    def _fix_old_neighbors(new_cuds_object, old_cuds_object, old_neighbors,
                           old_neighbor_diff):
        """Fix the relationships of the added Cuds objects.

        Fixes relationships to Cuds object that were previously neighbors.

        Args:
            new_cuds_object (Cuds): The added Cuds object
            old_cuds_object (Cuds, optional): The Cuds object that is going
                to be replaced
            old_neighbors (Iterator[Cuds]): The Cuds object that were neighbors
                before the replacement.
            old_neighbor_diff (List[Tuple[Union[UUID, URIRef], Relationship]]):
                The identifiers of the old neighbors and the relations they are
                connected with.
        """
        # iterate over all old neighbors.
        for (neighbor_identifier, relationship), neighbor \
                in zip(old_neighbor_diff, old_neighbors):
            inverse = relationship.inverse

            # delete the inverse if neighbors are children
            if relationship.is_subclass_of(cuba.activeRelationship):
                if inverse in neighbor._neighbors:
                    neighbor._remove_direct(inverse,
                                            new_cuds_object.identifier)

            # if neighbor is parent, add missing relationships
            else:
                if relationship not in new_cuds_object._neighbors:
                    new_cuds_object._neighbors[relationship] = {}
                for (identifier, oclasses), parent in \
                        zip(old_cuds_object._neighbors[relationship].items(),
                            neighbor._neighbors):
                    if parent is not None:
                        new_cuds_object \
                            ._neighbors[relationship][identifier] = oclasses

    def _add_direct(self, cuds_object, rel):
        """Add an cuds_object with a specific relationship.

        Args:
            cuds_object (Cuds): CUDS object to be added
            rel (OntologyRelationship): relationship with the cuds_object to
                add.
        """
        # First element, create set
        if rel not in self._neighbors.keys():
            self._neighbors[rel] = \
                {cuds_object.identifier: cuds_object.oclasses}
        # Element not already there
        elif cuds_object.identifier not in self._neighbors[rel]:
            self._neighbors[rel][cuds_object.identifier] = cuds_object.oclasses

    def _add_inverse(self, cuds_object, rel):
        """Add the inverse relationship from self to cuds_object.

        Args:
            cuds_object (Cuds): CUDS object to connect with.
            rel (OntologyRelationship): direct relationship
        """
        inverse_rel = rel.inverse
        self._add_direct(cuds_object, inverse_rel)

    def _get(self, *identifiers, rel=None, oclass=None, return_mapping=False):
        """Get the identifier of contained elements that satisfy the filter.

        This filter consists of a certain type, identifier or relationship.
        Expected calls are _get(), _get(*identifiers), _get(rel),_ get(oclass),
        _get(*identifiers, rel), _get(rel, oclass).
        If identifiers are specified, the result is the input, but
        non-available identifiers are replaced by None.

        Args:
            identifiers (Union[UUID, URIRef]): Identifiers of the elements to
                get.
            rel (OntologyRelationship, optional): Only return CUDS objects
                connected with a subclass of relationship. Defaults to None.
            oclass (OntologyClass, optional): Only return CUDS objects of a
                subclass of this ontology class. Defaults to None.
            return_mapping (bool, optional): Whether to return a mapping from
                identifiers to relationships, that connect self with the
                identifier. Defaults to False.

        Raises:
            TypeError: Specified both identifiers and oclass.
            ValueError: Wrong type of argument.

        Returns:
            List[Union[UUID, URIRef]] (+ Dict[Union[UUID, URIRef],
            Set[Relationship]]): list of identifiers, or None, if not found.
                (+ Mapping from UUIDs to relationships, which connect self to
                the respective Cuds object.)
        """
        if identifiers and oclass is not None:
            raise TypeError("Do not specify both identifiers and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise ValueError("Found object of type %s passed to argument rel. "
                             "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise ValueError("Found object of type %s passed to argument "
                             "oclass. Should be an OntologyClass."
                             % type(oclass))

        if identifiers:
            check_arguments((UUID, URIRef), *identifiers)

        self.session._notify_read(self)
        # consider either given relationship and subclasses
        # or all relationships.
        consider_relationships = set(self._neighbors.keys())
        if rel:
            consider_relationships &= set(rel.subclasses)
        consider_relationships = list(consider_relationships)

        # return empty list if no element of given relationship is available.
        if not consider_relationships and not return_mapping:
            return [] if not identifiers else [None] * len(identifiers)
        elif not consider_relationships:
            return ([], dict()) if not identifiers else \
                ([None] * len(identifiers), dict())

        if identifiers:
            return self._get_by_identifiers(identifiers,
                                            consider_relationships,
                                            return_mapping=return_mapping)
        return self._get_by_oclass(oclass, consider_relationships,
                                   return_mapping=return_mapping)

    def _get_by_identifiers(self, identifiers, relationships, return_mapping):
        """Check for each given identifier if it is connected by a given relationship.

        If not, replace it with None.
        Optionally return a mapping from identifiers to the set of
        relationships, which connect self and the cuds_object with the
        identifier.

        Args:
            identifiers (List[Union[UUID, URIRef]]): The identifiers to check.
            relationships (List[Relationship]): Only consider these
                relationships.
            return_mapping (bool): Whether to return a mapping from
                identifiers to relationships, that connect self with the
                identifier.

        Returns:
            List[Union[UUID, URIRef]] (+ Dict[Union[UUID, URIRef],
            Set[Relationship]]): list of found identifiers, None for not found
                identifiers (+ Mapping from identifiers to relationships, which
                connect self to the respective Cuds object.)
        """
        not_found_identifiers = dict(enumerate(identifiers)) if identifiers \
            else None
        relationship_mapping = dict()
        for relationship in relationships:

            # Identifiers are given.
            # Check which occur as object of current relation.
            found_identifiers_indexes = set()

            # we need to iterate over all identifiers for every
            # relationship if we compute a mapping
            iterator = enumerate(identifiers) if relationship_mapping \
                else not_found_identifiers.items()
            for i, identifier in iterator:
                if identifier in self._neighbors[relationship]:
                    found_identifiers_indexes.add(i)
                    if identifier not in relationship_mapping:
                        relationship_mapping[identifier] = set()
                    relationship_mapping[identifier].add(relationship)
            for i in found_identifiers_indexes:
                if i in not_found_identifiers:
                    del not_found_identifiers[i]

        collected_identifier = [(uid if i not in not_found_identifiers
                                 else None)
                                for i, uid in enumerate(identifiers)]
        if return_mapping:
            return collected_identifier, relationship_mapping
        return collected_identifier

    def _get_by_oclass(self, oclass, relationships, return_mapping):
        """Get the cuds_objects with given oclass.

        Only return objects that are connected to self
        with any of the given relationships. Optionally return a mapping
        from identifiers to the set of relationships, which connect self and
        the cuds_objects with the identifier.

        Args:
            oclass (OntologyClass, optional): Filter by the given
                OntologyClass. None means no filter.
            relationships (List[Relationship]): Filter by list of
                relationships.
            return_mapping (bool): whether to return a mapping from identifiers
            to relationships, that connect self with the identifier.

        Returns:
            List[Union[UUID, URIRef]] (+ Dict[Union[UUID, URIRef],
            Set[Relationship]]): The identifiers of the found CUDS objects
                (+ Mapping from identifier to set of relationsships that
                connect self with the respective cuds_object.)
        """
        relationship_mapping = dict()
        for relationship in relationships:

            # Collect all identifiers who are object of the current
            # relationship. Possibly filter by OntologyClass.
            for identifier, target_classes \
                    in self._neighbors[relationship].items():
                if oclass is None or any(t.is_subclass_of(oclass)
                                         for t in target_classes):
                    if identifier not in relationship_mapping:
                        relationship_mapping[identifier] = set()
                    relationship_mapping[identifier].add(relationship)
        if return_mapping:
            return list(relationship_mapping.keys()), relationship_mapping
        return list(relationship_mapping.keys())

    def _load_cuds_objects(self, identifiers):
        """Load the cuds_objects of the given identifiers from the session.

        Each in cuds_object is at the same position in the result as
        the corresponding identifier in the given identifier list.
        If the given identifiers contain None values, there will be
        None values at the same position in the result.

        Args:
            identifiers (List[Union[UUID, URIRef]]): The identifiers to fetch
            from the session.

        Yields:
            Cuds: The loaded cuds_objects
        """
        without_none = [identifier for identifier in identifiers
                        if identifier is not None]
        cuds_objects = self.session.load(*without_none)
        for identifier in identifiers:
            if identifier is None:
                yield None
            else:
                try:
                    yield next(cuds_objects)
                except StopIteration:
                    return None

    def _remove_direct(self, relationship, identifier):
        """Remove the direct relationship to the object with the given
        identifier.

        Args:
            relationship (OntologyRelationship): The relationship to remove.
            identifier (Union[UUID, URIRef]): The identifier to remove.
        """
        del self._neighbors[relationship][identifier]
        if not self._neighbors[relationship]:
            del self._neighbors[relationship]

    def _remove_inverse(self, relationship, identifier):
        """Remove the inverse of the given relationship.

        Args:
            relationship (OntologyRelationship): The relationship to remove.
            identifier (Union[UUID, URIRef]): The identifier to remove.
        """
        inverse = relationship.inverse
        self._remove_direct(inverse, identifier)

    def _check_valid_add(self, to_add, rel):
        return True  # TODO

    def __str__(self) -> str:
        """Get a human readable string.

        Returns:
            str: string with the Ontology class and identifier.
        """
        return "%s: %s" % (self.oclass, self.identifier)

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
            attr = self._get_attribute_by_argname(name)
            if self.session:
                self.session._notify_read(self)
            return self._graph.value(self.iri, attr.iri).toPython()
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
        self._graph.set((
            self.iri, attr.iri,
            Literal(attr.convert_to_datatype(new_value),
                    datatype=attr.datatype)
        ))
        if self.session:
            self.session._notify_update(self)

    def __repr__(self) -> str:
        """Return a machine readable string that represents the cuds object.

        Returns:
            str: Machine readable string representation for Cuds.
        """
        return "<%s: %s,  %s: @%s>" % (self.oclass, self.identifier,
                                       type(self.session).__name__,
                                       hex(id(self.session)))

    def __hash__(self) -> int:
        """Make Cuds objects hashable.

        Use the hash of the identifier of the object

        Returns:
            int: unique hash
        """
        return hash(self.identifier)

    def __eq__(self, other):
        """Define which CUDS objects are treated as equal.

        Same Ontology class and same identifier.

        Args:
            other (Cuds): Instance to check.

        Returns:
            bool: True if they share the identifier and class, False otherwise
        """
        return isinstance(other, Cuds) and other.oclass == self.oclass \
            and self.identifier == other.identifier

    def __getstate__(self):
        """Get the state for pickling or copying.

        Returns:
            Dict[str, Any]: The state of the object. Does not contain session.
                Contains the string of the OntologyClass.
        """
        state = {k: v for k, v in self.__dict__.items()
                 if k not in {"_session", "_graph"}}
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
