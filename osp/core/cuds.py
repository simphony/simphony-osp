"""A Common Universal Data Structure.

The CUDS object is an ontology individual that can be used like a container. It
has attributes and is connected to other cuds objects via relationships.
"""

import logging
from uuid import uuid4, UUID
from typing import Any, Dict, Generator, Iterable, Iterator, List, \
    MutableSet, Optional, Set, Tuple, Union

from rdflib import BNode, URIRef, RDF, Graph, Literal

from osp.core.namespaces import cuba, from_iri
from osp.core.neighbor_dict import NeighborDictRel
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.datatypes import CUDS_IRI_PREFIX, RDFCompatibleType, \
    RDF_COMPATIBLE_TYPES, UID
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.session.core_session import core_session
from osp.core.session.session import Session
from osp.core.utils.wrapper_development import check_arguments, \
    clone_cuds_object, create_from_cuds_object, get_neighbor_diff

logger = logging.getLogger("osp.core")

CUDS_NAMESPACE_IRI = URIRef(CUDS_IRI_PREFIX)


class Cuds:
    """A Common Universal Data Structure.

    The CUDS object is an ontology individual that can be used like a
    container. It has attributes and is connected to other cuds objects via
    relationships.
    """

    _session = core_session

    # Public API
    # ↓ ------ ↓

    @property
    def iri(self) -> URIRef:
        """Get the IRI of the CUDS object."""
        return self._uid.to_iri()

    @property
    def uid(self) -> UID:
        """Get the uid of the CUDS object.

        This is the public getter of the property.
        """
        return self._uid

    @property
    def session(self) -> Session:
        """Get the session of the cuds object."""
        return self._session

    @property
    def oclasses(self) -> List[OntologyClass]:
        """Get the ontology classes of this CUDS object."""
        result = list()
        for s, p, o in self._graph.triples((self.iri, RDF.type, None)):
            r = from_iri(o, raise_error=False)
            if r is not None:
                result.append(r)
        return result

    @property
    def oclass(self) -> Optional[OntologyClass]:
        """Get the type of the cuds object."""
        oclasses = self.oclasses
        if oclasses:
            return oclasses[0]
        return None

    def is_a(self, oclass) -> bool:
        """Check if the CUDS object is an instance of the given oclass.

        Args:
            oclass (OntologyClass): Check if the CUDS object is an instance of
                this oclass.

        Returns:
            bool: Whether the CUDS object is an instance of the given oclass.
        """
        return any(oc in oclass.subclasses for oc in self.oclasses)

    def __getattr__(self, name: str) -> RDFCompatibleType:
        """Retrieve an attribute whose domain matches the CUDS's oclass.

        Args:
            name: The name of the attribute.

        Raises:
            AttributeError: Unknown attribute name.

        Returns:
            The value of the attribute.
        """
        # TODO: The current behavior is to fail with non functional attributes.
        #  However, the check is based on the amount of values set for an
        #  attribute and not its definition as functional or non-functional
        #  in the ontology.
        # TODO: If an attribute whose domain is not explicitly specified was
        #  already fixed with __setitem__, then this should also give back
        #  such attributes (this is backwards compatible).
        try:
            attr = self._get_ontology_attribute_by_name(name)
            if self.session:
                self.session._notify_read(self)
            values = set(self._attribute_value_generator(attr))
            if len(values) > 1:
                raise RuntimeError(f"Tried to fetch values of a "
                                   f"non-functional attribute {attr} using "
                                   f"the dot notation. This is not "
                                   f"supported. "
                                   f"\n \n"
                                   f"Please use subscript "
                                   f"notation instead for such attributes: "
                                   f"my_cuds[{attr}]. This will return a set "
                                   f"of values instead of a single one")
            elif len(values) <= 0:
                return None
            else:
                return values.pop()
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

    def __setattr__(self, name: str,
                    values: Union[RDFCompatibleType,
                                  Set[RDFCompatibleType]]):
        """Set an attribute.

        Will notify the session if it corresponds to an ontology value.

        Args:
            name: The name of the attribute.
            values: The new value(s).

        Raises:
            AttributeError: Unknown attribute name.
        """
        if name.startswith("_"):
            super().__setattr__(name, values)
            return
        attr = self._get_ontology_attribute_by_name(name)
        values = {values} \
            if not isinstance(values, (Set, MutableSet)) \
            else values
        self._set_attributes(attr, values)

    def __setitem__(self,
                    rel: Union[OntologyAttribute, OntologyRelationship],
                    values: Union[
                        Union["Cuds", RDFCompatibleType],
                        Set[Union["Cuds", RDFCompatibleType]]],
                    ):
        """Manages both CUDS objects object properties and data properties.

        The subscripting syntax `cuds[rel] = ` allows,

        - when `rel` is an OntologyRelationship, to replace the list of CUDS
          that are connected to `cuds` through rel,
        - and when `rel` is an OntologyAttribute, to replace the values of
          such attribute.

        This function only accepts a set-like object as input, as the
        underlying RDF graph does not accept duplicate statements.

        Args:
            rel: Either an ontology attribute or an ontology relationship
            (OWL datatype property, OWL object property).
            values: Either a single element compatible with the OWL standard
            (this includes CUDS objects) or a set of such elements.

        Raises:
            TypeError: Trying to assign attributes using an object property,
                trying to assign cuds using a data property, trying to use
                something that is neither an OntologyAttribute or an
                OntologyRelationship as index.
        """
        values = {values} \
            if not isinstance(values, (Set, MutableSet)) \
            else values
        check_arguments((Cuds, *RDF_COMPATIBLE_TYPES), *values)
        cuds, literals = \
            tuple(filter(lambda x: isinstance(x, Cuds), values)), \
            tuple(filter(lambda x: isinstance(x, RDF_COMPATIBLE_TYPES),
                         values))
        # TODO: validating data types first and then splitting by data types
        #  sounds like redundancy and decrease in performance.

        if isinstance(rel, OntologyRelationship):
            if len(values) > 0:
                raise TypeError(f'Trying to assign attributes using an object'
                                f'property {rel}')
        elif isinstance(rel, OntologyAttribute):
            if len(cuds) > 0:
                raise TypeError(f'Trying to connect CUDS objects using '
                                f'a data property {rel}')

        if isinstance(rel, OntologyRelationship):
            for obj in self.iter(rel=rel):
                self.remove(obj)
            for obj in cuds:
                self.add(obj, rel=rel)
        elif isinstance(rel, OntologyAttribute):
            self._set_attributes(rel, literals)
        else:
            raise TypeError(f'CUDS objects indices must be ontology '
                            f'relationships or ontology attributes, '
                            f'not {type(rel)}')

    def __getitem__(self,
                    rel: Union[OntologyAttribute, OntologyRelationship]) \
            -> "Cuds._AttributeSet":
        """Retrieve linked CUDS objects objects or attribute values.

        The subscripting syntax `cuds[rel]` allows:

        - When `rel` is an OntologyRelationship, to obtain a set containing
          all CUDS objects that are connected to `cuds` through rel. Such
          set can be modified in-place to modify the existing connections.
        - When `rel` is an OntologyAttribute, to obtain a set containing all
          the values assigned to the specified attribute. Such set can be
          modified in-place to change the assigned values.

        The reason why a set is returned and not a list, or any other
        container allowing repeated elements, is that the underlying RDF
        graph does not accept duplicate statements.

        Args:
            rel: Either an ontology attribute or an ontology relationship (
            OWL datatype property, OWL object property).

        Raises:
            TypeError: Trying to use something that is neither an
                OntologyAttribute or an OntologyRelationship as index.
        """
        if isinstance(rel, OntologyAttribute):
            return self._AttributeSet(cuds=self, attribute=rel)
        elif isinstance(rel, OntologyRelationship):
            # TODO: Handle them with RelationshipSet as is done with
            #  attributes.
            return self._get(rel=rel)
        else:
            raise TypeError(f'CUDS objects indices must be ontology '
                            f'relationships or ontology attributes, '
                            f'not {type(rel)}')

    def add(self,
            *args: Any,
            rel: OntologyRelationship = None) -> Union["Cuds", List["Cuds"]]:
        """Link CUDS objects to another CUDS or assign data properties.

        If the added objects are associated with the same session,
        only a link is created. Otherwise, the a deepcopy is made and added
        to the session of this CUDS object.

        Before adding, check for invalid keys to avoid inconsistencies later.

        Args:
            args (Cuds): The objects to be added
            rel (OntologyRelationship): The relationship between the objects.

        Raises:
            TypeError: No relationship given and no default specified.
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
            *[arg.uid for arg in args if arg.session != self.session])
        for arg in args:
            # Recursively add the children to the registry
            if rel in self._neighbors \
                    and arg.uid in self._neighbors[rel]:
                message = '{!r} is already in the container'
                raise ValueError(message.format(arg))
            if self.session != arg.session:
                arg = self._recursive_store(arg, next(old_objects))

            self._add_direct(arg, rel)
            arg._add_inverse(self, rel)
            result.append(arg)
        return result[0] if len(args) == 1 else result

    def get(self,
            *uids: Union[UUID, URIRef, UID],
            rel: OntologyRelationship = cuba.activeRelationship,
            oclass: OntologyClass = None,
            return_rel: bool = False) -> Union["Cuds", List["Cuds"]]:
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
            self.iter(*uids, rel=rel, oclass=oclass,
                      return_rel=return_rel)
        )
        if len(uids) == 1:
            return result[0]
        return result

    def iter(self,
             *uids: Union[UUID, URIRef, UID],
             rel: OntologyRelationship = cuba.activeRelationship,
             oclass: OntologyClass = None,
             return_rel: bool = False) -> Iterator["Cuds"]:
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
            uids (Union[UUID, URIRef, UID]): uids of the elements.
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

    def update(self, *args: "Cuds") -> Union["Cuds", List["Cuds"]]:
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
        _, relationship_mapping = self._get(*uids, rel=rel,
                                            oclass=oclass, return_mapping=True)
        if not relationship_mapping:
            raise RuntimeError("Did not remove any Cuds object, "
                               "because none matched your filter.")
        uid_relationships = list(relationship_mapping.items())

        # load all the neighbors to delete and remove inverse relationship
        neighbors = self.session.load(
            *[uid for uid, _ in uid_relationships])
        for uid_relationship, neighbor in zip(uid_relationships,
                                              neighbors):
            uid, relationships = uid_relationship
            for relationship in relationships:
                self._remove_direct(relationship, uid)
                neighbor._remove_inverse(relationship, self.uid)

    # ↑ ------ ↑
    # Public API

    def __init__(self,
                 # Create from oclass and attributes dict.
                 attributes: Dict[OntologyAttribute, Set[Any]],
                 oclass: Optional[OntologyClass] = None,
                 session: Session = None,
                 uid: Optional[UID] = None,
                 # Specify extra triples for the CUDS object.
                 extra_triples: Iterable[
                     Tuple[Union[URIRef, BNode],
                           Union[URIRef, BNode],
                           Union[URIRef, BNode]]] = tuple()):
        """Initialize a CUDS object."""
        if uid is None:
            uid = UID()
        elif not isinstance(uid, UID):
            raise Exception(f"Tried to initialize a CUDS object with a uid "
                            f"which is not a UID object.")
        self._uid = uid

        # Create CUDS triples in internal temporary graph.
        self._graph = Graph()
        if attributes:
            for k, v in attributes.items():
                for e in v:
                    self._graph.add((
                        self.iri, k.iri, Literal(k.convert_to_datatype(e),
                                                 datatype=k.datatype)
                    ))
        if oclass:
            self._graph.add((
                self.iri, RDF.type, oclass.iri
            ))
        extra_oclass = False
        for s, p, o in extra_triples:
            if s != self.iri:
                raise ValueError("Trying to add extra triples to a CUDS "
                                 "object with a subject that does not match "
                                 "the CUDS object's IRI.")
            elif p == RDF.type:
                extra_oclass = True
            self._graph.add((s, p, o))
        oclass_assigned = bool(oclass) or extra_oclass
        if not oclass_assigned:
            raise TypeError(f"No oclass associated with {self}! "
                            f"Did you install the required ontology?")

        self._session = session or Cuds._session
        # Copy temporary graph to the session graph and discard it.
        self.session._store(self)

    @property
    def _uid(self) -> UID:
        """Get the uid of the CUDS object.

        This is the private getter of the property.
        """
        return self.__uid

    @_uid.setter
    def _uid(self, value: UID):
        """Set the uid of a CUDS object.

        This is the private setter of the property.
        """
        self.__uid = value

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

    # Attribute handling
    # ↓ -------------- ↓

    def get_attributes(self) -> Dict[OntologyAttribute,
                                     Set[RDFCompatibleType]]:
        """Get the attributes as a dictionary."""
        return {attribute: set(value_generator)
                for attribute, value_generator
                in self._attribute_and_value_generator()}

    def _get_ontology_attribute_by_name(self, name: str) -> OntologyAttribute:
        """Get the attributes of this CUDS by argname."""
        for oclass in self.oclasses:
            attr = oclass.get_attribute_by_argname(name)
            if attr is not None:
                return attr
        raise AttributeError(name)

    def _add_attributes(self,
                        attribute: OntologyAttribute,
                        values: Iterable[RDFCompatibleType]):
        """Add values to a datatype property.

        If any of the values provided in `values` have already been assigned,
        then they are simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of Pyhon types that are compatible either
                with the OWL standard's datatypes for literals or compatible
                with OSP-core as custom datatypes.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom datatypes are given.
        """
        # TODO: prevent the end result having more than one value than one
        #  depending on ontology cardinality restrictions and/or functional
        #  property criteria.
        values = set(values)
        for x in values:
            if not isinstance(x, RDF_COMPATIBLE_TYPES):
                raise TypeError(f"Type '{type(x)}' of object {x} cannot "
                                f"be set as attribute value, as it is "
                                f"incompatible with the OWL standard")
        if self.session:
            self.session._notify_read(self)
        for value in values:
            self._graph.add((self.iri, attribute.iri,
                             Literal(attribute.convert_to_datatype(value),
                                     datatype=attribute.datatype)))
        if self.session:
            self.session._notify_update(self)

    def _delete_attributes(self,
                           attribute: OntologyAttribute,
                           values: Iterable[RDFCompatibleType]):
        """Remove values from a datatype property.

        If any of the values provided in `values` are not present, they are
        simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of Pyhon types that are compatible either
                with the OWL standard's datatypes for literals or compatible
                with OSP-core as custom datatypes.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom datatypes are given.
        """
        values = set(values)
        for x in values:
            if not isinstance(x, RDF_COMPATIBLE_TYPES):
                logger.warning(f"Type '{type(x)}' of object {x} cannot "
                               f"be an attribute value, as it is "
                               f"incompatible with the OWL standard")
        if self.session:
            self.session._notify_read(self)
        for value in values:
            self._graph.remove((self.iri, attribute.iri,
                                Literal(attribute.convert_to_datatype(value),
                                        datatype=attribute.datatype)))
        if self.session:
            self.session._notify_update(self)

    def _set_attributes(self,
                        attribute: OntologyAttribute,
                        values: Iterable[RDFCompatibleType]):
        """Replace values assigned to a datatype property.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of Pyhon types that are compatible either
                with the OWL standard's datatypes for literals or compatible
                with OSP-core as custom datatypes.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom datatypes are given.
        """
        # TODO: prevent the end result having more than one value than one
        #  depending on ontology cardinality restrictions and/or functional
        #  property criteria.
        values = set(values)
        for x in values:
            if not isinstance(x, RDF_COMPATIBLE_TYPES):
                logger.warning(f"Type '{type(x)}' of object {x} cannot "
                               f"be set as attribute value, as it is "
                               f"incompatible with the OWL standard")
        if self.session:
            self.session._notify_read(self)
        self._graph.remove((self.iri, attribute.iri, None))
        for value in values:
            self._graph.add((self.iri, attribute.iri,
                             Literal(attribute.convert_to_datatype(value),
                                     datatype=attribute.datatype)))
        if self.session:
            self.session._notify_update(self)

    def _attribute_value_generator(self,
                                   attribute: OntologyAttribute,
                                   _notify_read: bool = True) \
            -> Generator[RDFCompatibleType, None, None]:
        """Returns a generator of values assigned to the specified attribute.

        Args:
            attribute: The ontology attribute query for values.

        Returns:
            Generator that returns the attribute values.
        """
        if _notify_read and self.session:
            self.session._notify_read(self)
        for literal in self._graph.objects(self.iri, attribute.iri):
            yield literal.toPython()

    def _attribute_generator(self, _notify_read: bool = True) \
            -> Generator[OntologyAttribute, None, None]:
        """Returns a generator of the attributes of this CUDS object.

        The generator only returns the OntologyAttribute objects, NOT the
        values.

        Returns:
            Generator that returns the attributes of this CUDS object.
        """
        if _notify_read and self.session:
            self.session._notify_read(self)
        for predicate in self._graph.predicates(self.iri, None):
            obj = from_iri(predicate, raise_error=False)
            if isinstance(obj, OntologyAttribute):
                yield obj

    def _attribute_and_value_generator(self, _notify_read: bool = True) \
            -> Generator[Tuple[OntologyAttribute,
                         Generator[RDFCompatibleType, None, None]],
                         None, None]:
        """Returns a generator of the both attributes and their values.

        Returns:
            Generator that yields tuples, where the first item is the ontology
            attribute and the second a generator of values for such attribute.
        """
        if _notify_read and self.session:
            self.session._notify_read(self)
        for attribute in self._attribute_generator(_notify_read=False):
            yield attribute,\
                self._attribute_value_generator(attribute,
                                                _notify_read=False)

    class _AttributeSet(MutableSet):
        """A set interface to a CUDS object's attributes.

        This class looks like and acts like the standard `set`, but it
        is an interface to the `_add_attributes`, _set_attributes`,
        `_delete_attributes`, `_attribute_value_generator` functions.

        When an instance is read, the method `_attribute_value_generator` is
        used to fetch the data. When it is modified in-place, the methods
        `_add_attributes`, `_set_attributes`, and `_delete_attributes` are used
        to reflect the changes.

        This class does not hold any attribute-related information itself, thus
        it is safe to spawn multiple instances linked to the same attribute
        and CUDS (when single-threading).
        """
        _attribute: OntologyAttribute
        _cuds: "Cuds"

        @property
        def _underlying_set(self) -> Set:
            """The set of values assigned to the attribute `self._attribute`.

            Returns:
                The mentioned underlying set.
            """
            return set(
                self._cuds._attribute_value_generator(
                    attribute=self._attribute))

        def __init__(self, attribute: OntologyAttribute, cuds: "Cuds"):
            """Fix the liked OntologyAttribute and CUDS object."""
            self._cuds = cuds
            self._attribute = attribute
            super().__init__()

        def __repr__(self) -> str:
            """Return repr(self)."""
            return self._underlying_set.__repr__() \
                + f' <{self._attribute} of CUDS {self._cuds}>'

        def __str__(self) -> str:
            """Return str(self)."""
            return self._underlying_set.__str__()

        def __format__(self, format_spec) -> str:
            """Default object formatter."""
            return self._underlying_set.__format__(format_spec)

        def __contains__(self, item: Any) -> bool:
            """Return y in x."""
            for x in self._underlying_set:
                if x == item:
                    return True
            else:
                return False

        def __iter__(self):
            """Implement iter(self)."""
            for x in self._underlying_set:
                yield x

        def __len__(self) -> int:
            """Return len(self)."""
            i = 0
            for x in self._cuds._attribute_value_generator(
                    attribute=self._attribute):
                i += 1
            return i

        def __le__(self, other: set) -> bool:
            """Return self<=other."""
            return self._underlying_set.__le__(other)

        def __lt__(self, other: set) -> bool:
            """Return self<other."""
            return self._underlying_set.__lt__(other)

        def __eq__(self, other: set) -> bool:
            """Return self==other."""
            return self._underlying_set.__eq__(other)

        def __ne__(self, other: set) -> bool:
            """Return self!=other."""
            return self._underlying_set.__ne__(other)

        def __gt__(self, other: set) -> bool:
            """Return self>other."""
            return self._underlying_set.__gt__(other)

        def __ge__(self, other: set) -> bool:
            """Return self>=other."""
            return self._underlying_set.__ge__(other)

        def __and__(self, other: set) -> Set[RDFCompatibleType]:
            """Return self&other."""
            return self._underlying_set.__and__(other)

        def __or__(self, other: set) -> set:
            """Return self|other."""
            return self._underlying_set.__or__(other)

        def __sub__(self, other: set) -> Set[RDFCompatibleType]:
            """Return self-other."""
            return self._underlying_set.__sub__(other)

        def __xor__(self, other: set) -> Set:
            """Return self^other."""
            return self._underlying_set.__xor__(other)

        def __ior__(self, other: Set[RDFCompatibleType]):
            """Return self|=other."""
            self._cuds._add_attributes(self._attribute, other)
            return self

        def __iand__(self, other: Set):
            """Return self&=other."""
            underlying_set = self._underlying_set
            intersection = underlying_set.intersection(other)
            removed = underlying_set.difference(intersection)
            self._cuds._delete_attributes(self._attribute, removed)
            return self

        def __ixor__(self, other: Set[RDFCompatibleType]):
            """Return self^=other."""
            self._cuds._set_attributes(self._attribute,
                                       self._underlying_set ^ other)
            return self

        def __iadd__(self, other: Set[RDFCompatibleType]):
            """Return self+=other (equivalent to self|=other)."""
            return self.__ior__(other)

        def __isub__(self, other: set):
            """Return self-=other."""
            self._cuds._delete_attributes(self._attribute,
                                          self._underlying_set & other)
            return self

        def isdisjoint(self, other: set):
            """Return True if two sets have a null intersection."""
            return self._underlying_set.isdisjoint(other)

        def clear(self):
            """Remove all elements from this set.

            This also removed all the values assigned to the attribute
            linked to this set for the cuds linked to this set.
            """
            self._cuds._set_attributes(self._attribute, set())

        def pop(self) -> RDFCompatibleType:
            """Remove and return an arbitrary set element.

            Raises KeyError if the set is empty.
            """
            result = self._underlying_set.pop()
            self._cuds._delete_attributes(self._attribute, {result})
            return result

        def copy(self):
            """Return a shallow copy of a set."""
            return self._underlying_set

        def difference(self, other: Iterable) -> Set[RDFCompatibleType]:
            """Return the difference of two or more sets as a new set.

            (i.e. all elements that are in this set but not the others.)
            """
            return self._underlying_set.difference(other)

        def difference_update(self, other: Iterable):
            """Remove all elements of another set from this set."""
            self._cuds._delete_attributes(
                self._attribute, self._underlying_set.intersection(other))

        def discard(self, other: Any):
            """Remove an element from a set if it is a member.

            If the element is not a member, do nothing.
            """
            self._cuds._delete_attributes(self._attribute, {other})

        def intersection(self, other: set) -> Set[RDFCompatibleType]:
            """Return the intersection of two sets as a new set.

            (i.e. all elements that are in both sets.)
            """
            return self._underlying_set.intersection(other)

        def intersection_update(self, other: set):
            """Update a set with the intersection of itself and another."""
            self.__iand__(other)

        def issubset(self, other: set) -> bool:
            """Report whether another set contains this set."""
            return self <= other

        def issuperset(self, other: set) -> bool:
            """Report whether this set contains another set."""
            return self >= other

        def add(self, other: RDFCompatibleType):
            """Add an element to a set.

            This has no effect if the element is already present.
            """
            self.__ior__({other})

        def remove(self, other: Any):
            """Remove an element from a set; it must be a member.

            If the element is not a member, raise a KeyError.
            """
            if other in self._underlying_set:
                self._cuds._delete_attributes(self._attribute, {other})
            else:
                raise KeyError(f"{other}")

        def update(self, other: Iterable):
            """Update a set with the union of itself and others."""
            self._cuds._add_attributes(
                self._attribute, set(other).difference(self._underlying_set))

    # ↑ -------------- ↑
    # Attribute handling

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
                for child_uid in \
                        new_cuds_object._neighbors[outgoing_rel]:
                    if child_uid not in uids_stored:
                        new_child = new_child_getter.get(
                            child_uid, rel=outgoing_rel)
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
            new_cuds_object, old_cuds_object, mode="non-active")
        # get the neighbors that were neighbors
        # before adding the new cuds_object
        old_neighbor_diff = get_neighbor_diff(old_cuds_object,
                                              new_cuds_object)

        # Load all the cuds_objects of the session
        cuds_objects = iter(session.load(
            *[uid for uid, _ in
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
                         new_parent_diff: List[Tuple[Union[UUID, URIRef],
                                                     OntologyRelationship]],
                         missing):
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
        for (parent_uid, relationship), parent in zip(new_parent_diff,
                                                      new_parents):
            if relationship.is_subclass_of(cuba.activeRelationship):
                continue
            inverse = relationship.inverse
            # Delete connection to parent if parent is not present
            if parent is None:
                if parent_uid not in missing:
                    missing[parent_uid] = list()
                missing[parent_uid].append((new_cuds_object,
                                            relationship))
                continue

            # Add the inverse to the parent
            if inverse not in parent._neighbors:
                parent._neighbors[inverse] = {}

            parent._neighbors[inverse][new_cuds_object.uid] = \
                new_cuds_object.oclasses

    @staticmethod
    def _fix_old_neighbors(new_cuds_object, old_cuds_object,
                           old_neighbors: List[Tuple[Union[UUID, URIRef],
                                                     OntologyRelationship]],
                           old_neighbor_diff):
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
        for (neighbor_uid, relationship), neighbor \
                in zip(old_neighbor_diff, old_neighbors):
            inverse = relationship.inverse

            # delete the inverse if neighbors are children
            if relationship.is_subclass_of(cuba.activeRelationship):
                if inverse in neighbor._neighbors:
                    neighbor._remove_direct(inverse,
                                            new_cuds_object.uid)

            # if neighbor is parent, add missing relationships
            else:
                if relationship not in new_cuds_object._neighbors:
                    new_cuds_object._neighbors[relationship] = {}
                for (uid, oclasses), parent in \
                        zip(old_cuds_object._neighbors[relationship].items(),
                            neighbor._neighbors):
                    if parent is not None:
                        new_cuds_object \
                            ._neighbors[relationship][uid] = oclasses

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
                {cuds_object.uid: cuds_object.oclasses}
        # Element not already there
        elif cuds_object.uid not in self._neighbors[rel]:
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
            raise ValueError("Found object of type %s passed to argument rel. "
                             "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise ValueError("Found object of type %s passed to argument "
                             "oclass. Should be an OntologyClass."
                             % type(oclass))

        if uids:
            check_arguments(UID, *uids)

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
            return ([], dict()) if not uids else \
                ([None] * len(uids), dict())

        if uids:
            return self._get_by_uids(uids, consider_relationships,
                                     return_mapping=return_mapping)
        return self._get_by_oclass(oclass, consider_relationships,
                                   return_mapping=return_mapping)

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
        not_found_uids = dict(enumerate(uids)) if uids \
            else None
        relationship_mapping = dict()
        for relationship in relationships:

            # uids are given.
            # Check which occur as object of current relation.
            found_uids_indexes = set()

            # we need to iterate over all uids for every
            # relationship if we compute a mapping
            iterator = enumerate(uids) if relationship_mapping \
                else not_found_uids.items()
            for i, uid in iterator:
                if uid in self._neighbors[relationship]:
                    found_uids_indexes.add(i)
                    if uid not in relationship_mapping:
                        relationship_mapping[uid] = set()
                    relationship_mapping[uid].add(relationship)
            for i in found_uids_indexes:
                if i in not_found_uids:
                    del not_found_uids[i]

        collected_uid = [(uid if i not in not_found_uids
                          else None)
                         for i, uid in enumerate(uids)]
        if return_mapping:
            return collected_uid, relationship_mapping
        return collected_uid

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
            for uid, target_classes \
                    in self._neighbors[relationship].items():
                if oclass is None or any(t.is_subclass_of(oclass)
                                         for t in target_classes):
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
            uids (List[Union[UUID, URIRef]]): The uids to fetch from the
                session.

        Yields:
            Cuds: The loaded cuds_objects
        """
        without_none = [uid for uid in uids
                        if uid is not None]
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

    def __repr__(self) -> str:
        """Return a machine readable string that represents the cuds object.

        Returns:
            str: Machine readable string representation for Cuds.
        """
        return "<%s: %s,  %s: @%s>" % (self.oclass, self.uid,
                                       type(self.session).__name__,
                                       hex(id(self.session)))

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
        return isinstance(other, Cuds) and other.oclass == self.oclass \
            and self.uid == other.uid

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
