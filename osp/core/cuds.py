"""A Common Universal Data Structure.

The CUDS object is an ontology individual that can be used like a container. It
has attributes and is connected to other cuds objects via relationships.
"""
import functools
import itertools
import logging
from collections import OrderedDict
from typing import Dict, Iterable, Iterator, List, \
    MutableSet, Optional, Set, Tuple, Union
from uuid import UUID

from rdflib import BNode, Graph, Literal, RDF, URIRef

from osp.core.namespaces import cuba, from_iri
from osp.core.neighbor_dict import NeighborDictRel
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.datatypes import CUDS_IRI_PREFIX, RDFCompatibleType, \
    RDF_COMPATIBLE_TYPES, UID
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.utils import DataStructureSet
from osp.core.session.core_session import core_session
from osp.core.session.result import MultipleResultsError, ResultEmptyError
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

    def __init__(self,
                 # Create from oclass and attributes dict.
                 attributes: Dict[OntologyAttribute,
                                  Iterable[RDFCompatibleType]],
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
            raise Exception(f"Tried to initialize a CUDS object with uid "
                            f"{uid}, which is not a UID object.")
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
        for o in self._graph.objects(self.iri, RDF.type):
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
            if self.session:
                # Notify the read before getting the attribute by name, as CUDS
                #  in the deleted buffer may change class to None if done this
                #  way, making `_get_ontology_attribute_by_name` raise an
                #  attribute error for such case as it should be.
                self.session._notify_read(self)
            attr = self._get_ontology_attribute_by_name(name)
            values = set(self._attribute_value_generator(attr,
                                                         _notify_read=False))
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
                    value: Optional[Union[RDFCompatibleType,
                                          Set[RDFCompatibleType]]]):
        """Set an attribute.

        Will notify the session if it corresponds to an ontology value.

        Args:
            name: The name of the attribute.
            value: The new value.

        Raises:
            AttributeError: Unknown attribute name.
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        attr = self._get_ontology_attribute_by_name(name)
        value = {value} if value is not None else set()
        self._set_attributes(attr, value)

    def __setitem__(self,
                    rel: Union[OntologyAttribute, OntologyRelationship],
                    values: Optional[Union[
                        Union["Cuds", RDFCompatibleType],
                        Union[Set["Cuds"], Set[RDFCompatibleType]]
                    ]],
                    ):
        """Manages both CUDS objects object properties and data properties.

        The subscripting syntax `cuds[rel] = ` allows,

        - when `rel` is an OntologyRelationship, to replace the list of CUDS
          that are connected to `cuds` through rel,
        - and when `rel` is an OntologyAttribute, to replace the values of
          such attribute.

        This function only accepts hashable objects as input, as the
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
        if isinstance(values, Cuds._ObjectSet) \
                and values.cuds is self and values.predicate is rel:
            # Do not do anything when the set assigned is a set referring to
            #  self and referring to the same predicate that was specified.
            #  Avoids duplication of work that would happen because
            #  `x[c] += y <-> x[c] == x[c].__iadd__(y)`. An alternative is
            #  getting rid of `__iadd__` so that
            #  `x[c] += y <-> x[c] = x[c] + y`. But this implies
            #  incompatibilities with `collections.ABC` (they already define
            #  `__isub__` for MutableSet for example).
            return

        values = values or set()
        values = {values} \
            if not isinstance(values, (Set, MutableSet)) \
            else values
        # Apparently instances of MutableSet are not instances of Set.

        # Split values into cuds and values compatible with literals.
        cuds, literals = \
            set(filter(lambda x: isinstance(x, Cuds), values)), \
            set(filter(lambda x: isinstance(x, RDF_COMPATIBLE_TYPES),
                       values))

        if len(cuds) + len(literals) != len(values):
            illegal_types = (
                type(x) for x in values - (cuds | literals))
            raise TypeError("Expected values of type 'Cuds' or "
                            "'RDFCompatibleType', got %s." %
                            ', '.join(illegal_types))
        elif isinstance(rel, OntologyRelationship):
            if len(literals) > 0:
                raise TypeError(f'Trying to assign attributes using an object'
                                f'property {rel}')
            relationship_set = Cuds._RelationshipSet(rel, self, oclass=None)
            add, remove = cuds - relationship_set, relationship_set - cuds
            relationship_set |= add
            relationship_set -= remove
        elif isinstance(rel, OntologyAttribute):
            if len(cuds) > 0:
                raise TypeError(f'Trying to connect CUDS objects using '
                                f'a data property {rel}')
            attribute_set = Cuds._AttributeSet(rel, self)
            add = literals - attribute_set
            remove = attribute_set - literals
            attribute_set |= add
            attribute_set -= remove
        else:
            raise TypeError(f'CUDS objects indices must be ontology '
                            f'relationships or ontology attributes, '
                            f'not {type(rel)}')

    def __getitem__(self,
                    rel: Union[OntologyAttribute, OntologyRelationship]) \
            -> Union["Cuds._AttributeSet", "Cuds._RelationshipSet"]:
        """Retrieve linked CUDS objects objects or attribute values.

        The subscripting syntax `cuds[rel]` allows:
        - When `rel` is an OntologyAttribute, to obtain a set containing all
          the values assigned to the specified attribute. Such set can be
          modified in-place to change the assigned values.
        - When `rel` is an OntologyRelationship, to obtain a set containing
          all CUDS objects that are connected to `cuds` through rel. Such
          set can be modified in-place to modify the existing connections.

        The reason why a set is returned and not a list, or any other
        container allowing repeated elements, is that the underlying RDF
        graph does not accept duplicate statements.

        Args:
            rel: An ontology attribute or an ontology relationship
                (OWL datatype property, OWL object property).

        Returns:
            Either a "Cuds._AttributeSet" or "Cuds._Relationship" for the
            given attribute or relationship.

        Raises:
            TypeError: Trying to use something that is neither an
                OntologyAttribute or an OntologyRelationship as index.
        """
        if isinstance(rel, OntologyAttribute):
            class_ = self._AttributeSet
        elif isinstance(rel, OntologyRelationship):
            class_ = self._RelationshipSet
        else:
            raise TypeError(f'CUDS objects indices must be ontology '
                            f'relationships or ontology attributes, '
                            f'not {type(rel)}')

        return class_(rel, self)

    def __delitem__(self, rel: Union[OntologyAttribute, OntologyRelationship]):
        """Delete all attributes or data properties attached through rel.

        Args:
            rel: Either an ontology attribute or an ontology relationship
                (OWL datatype property, OWL object property).
        """
        self.__setitem__(rel=rel, values=set())

    def add(self,
            *cuds: "Cuds",
            rel: Optional[OntologyRelationship] = None) -> Union["Cuds",
                                                                 List["Cuds"]]:
        """Link CUDS objects to another CUDS objects.

        If the added objects are associated with the same session,
        only a link is created. Otherwise, the a deepcopy is made and added
        to the session of this CUDS object.

        Args:
            cuds: The objects to be added
            rel: The relationship between the objects.

        Raises:
            TypeError: Either
                - no relationship given and no default specified, or
                - objects not of type CUDS provided as positional arguments.
            ValueError: Added a CUDS object that is already in the
                container. Note: in fact, the exception raised is
                `ExistingCudsException`, but it is a subclass of `ValueError`.

        Returns:
            The CUDS objects that have been added, associated with the
            session of the current CUDS object. The result type is a list
            if more than one CUDS object was provided.
        """
        check_arguments(Cuds, *cuds)
        rel = rel or self.oclass.namespace.get_default_rel()
        if rel is None:
            raise TypeError("Missing argument 'rel'! No default "
                            "relationship specified for namespace %s."
                            % self.oclass.namespace)

        result = self._connect(*cuds, rel=rel)
        return result[0] if len(cuds) == 1 else result

    class ExistingCudsException(ValueError):
        """To be raised when a provided CUDS is already linked."""
        pass

    def get(self,
            *uids: UID,
            rel: Optional[OntologyRelationship] = cuba.activeRelationship,
            oclass: OntologyClass = None,
            return_rel: bool = False) -> Union[
        "Cuds._RelationshipSet",
        Optional["Cuds"],
        Tuple[Optional["Cuds"], ...],
        Tuple[Tuple["Cuds", OntologyRelationship]]
    ]:
        """Return the contained elements.

        Only return objects with given uids, connected through a certain
        relationship and its sub-relationships and optionally filter by oclass.

        Expected calls are get(), get(rel=___), get(oclass=___),
        get(rel=___, oclass=___), get(*uids), get(*uids, rel=___). In
        addition, all the previous calls are possible with the argument
        `return_rel=True`. The structure of the output can vary depending on
        the form used for the call. See the "Returns:" section of this
        docstring for more details on this..

        Args:
            uids: Filter the elements to be returned by their UIDs.
            rel: Filters allowing only CUDS objects which are connected by a
                subclass of the given relationship. Defaults to
                cuba.activeRelationship. When none, all relationships are
                accepted.
            oclass: Only return elements which are a subclass of the given
                ontology class. Defaults to None (no filter).
            return_rel: Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Calls without `*uids` (_RelationshipSet): The result of the
                call is a set-like object. This corresponds to
                the calls `get()`, `get(rel=___)`, `get(oclass=___)`,
                `get(rel=___, oclass=___)`, with the parameter `return_rel`
                unset or set to False.
            Calls with `uids` (Optional["Cuds"],
                    Tuple[Optional["Cuds"], ...]):
                The position of each element in the result is determined by
                the position of the corresponding UID in the given list of
                UIDs. In this case, the result can contain `None` values if
                a given UID is not a child of this CUDS object. When only
                one UID is specified, a single object is returned instead of a
                Tuple. This description corresponds to the calls `get(*uids)`,
                `get(*uids, rel=___)`.
            Calls with `return_rel=True` (Tuple[
                    Tuple["Cuds", OntologyRelationship]]):
                The dependence of the order of the elements is maintained
                for the calls with `uids`, a non-deterministic order is used
                for the calls without `uids`. No `None` values are contained
                in the result (such UIDs are simply skipped).
                Moreover, the elements returned are now pairs of CUDS
                objects and the relationship connecting such object to this
                one. When only one UID is specified, a single pair is
                returned instead of a Tuple. This description corresponds to
                any call of the form `get(..., return_rel=True)`.
        """
        if not return_rel and not uids:
            result = Cuds._RelationshipSet(rel, self, oclass=oclass)
        else:
            result = tuple(
                self.iter(*uids, rel=rel, oclass=oclass,
                          return_rel=return_rel)
            )
            if len(uids) == 1:
                result = result[0]
        return result

    def iter(self,
             *uids: UID,
             rel: Optional[OntologyRelationship] = cuba.activeRelationship,
             oclass: Optional[OntologyClass] = None,
             return_rel: bool = False) -> Union[
        Iterator["Cuds"],
        Iterator[Optional["Cuds"]],
        Iterator[Tuple["Cuds", OntologyRelationship]],
    ]:
        """Iterate over the contained elements.

        Only iterate over objects with given uids, connected through a certain
        relationship and its sub-relationships and optionally filter by oclass.

        Expected calls are iter(), iter(rel=___), iter(oclass=___),
        iter(rel=___, oclass=___), iter(*uids), iter(*uids, rel=___). In
        addition, all the previous calls are possible with the argument
        `return_rel=True`. The structure of the output can vary depending on
        the form used for the call. See the "Returns:" section of this
        docstring for more details on this.

        Args:
            uids: Filter the elements to be returned by their UIDs.
            rel: Filters allowing only CUDS objects which are connected by a
                subclass of the given relationship. Defaults to
                cuba.activeRelationship. When none, all relationships are
                accepted.
            oclass: Only return elements which are a subclass of the given
                ontology class. Defaults to None (no filter).
            return_rel: Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Calls without `*uids` (Iterator["Cuds"]): The position of each
                element in the result is non-deterministic. This corresponds to
                the calls `iter()`, `iter(rel=___)`, `iter(oclass=___)`,
                `iter(rel=___, oclass=___)`, with the parameter `return_rel`
                unset or set to False.
            Calls with `uids` (Iterator[Optional["Cuds"]]): The position of
                each element in the result is determined by the position of
                the corresponding UID in the given list of UIDs. In this
                case, the result can contain `None` values if a given UID is
                not a child of this CUDS object. This corresponds to the calls
                `iter(*uids)`, `iter(*uids, rel=___)`.
            Calls with `return_rel=True` (Iterator[
                    Tuple["Cuds", OntologyRelationship]]):
                The dependence of the order of the elements on whether
                `uids` are specified or not is maintained, no `None` values
                are contained in the result (such UIDs are simply skipped).
                Moreover, the elements returned are now pairs of CUDS
                objects and the relationship connecting such object to this
                one. This corresponds to any call of the form
                `iter(..., return_rel=True)`.

        Raises:
            TypeError: Incorrect argument types.
            ValueError: Both UIDs and an ontology class passed to the function.
        """
        if uids and oclass is not None:
            raise ValueError("Do not specify both uids and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise TypeError("Found object of type %s passed to argument rel. "
                            "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError("Found object of type %s passed to argument "
                            "oclass. Should be an OntologyClass."
                            % type(oclass))

        # --- Call without `*uids` and with `return_rel=False`(order does not
        #  matter, relationships not returned).
        if not return_rel and not uids:
            yield from iter(Cuds._RelationshipSet(rel, self, oclass=oclass))
            return

        # --- Call with `uids`.

        self.session._notify_read(self)

        # Consider either the given relationship and subclasses or all
        #  relationships.
        consider_relationships = set(self._neighbors)
        if rel:
            consider_relationships &= set(rel.subclasses)

        # return empty list if no element of given relationship is available.
        if not consider_relationships:
            yield from \
                [] if not uids else [None] * len(uids) \
                if not return_rel else \
                ([], dict()) if not uids else ([None] * len(uids), dict())
            return

        mapping = OrderedDict() if not uids else \
            OrderedDict((uid, set()) for uid in uids)
        for rel in consider_relationships:
            result_uids = self._iter(*uids, rel=rel, oclass=oclass,
                                     notify_read=False)
            if uids:
                result_uids = filter(None, result_uids)
            mapping.update(OrderedDict(
                (uid, mapping.get(uid, set()) | {rel})
                for uid in result_uids
            ))

        to_load = (uid if mapping[uid] else None for uid in mapping)
        result = self._load_cuds_objects(to_load)

        if not return_rel:
            yield from result
        else:
            yield from ((r, m) for r in result for m in mapping[r.uid])

    def update(self, *args: "Cuds") -> Union["Cuds", List["Cuds"]]:
        """Update the Cuds object.

        Updates the object by providing updated versions of CUDS objects
        that are directly in the container of this CUDS object.
        The updated versions must be associated with a different session.

        Args:
            args: The updated versions to use to update the current object.

        Raises:
            ValueError: Provided a CUDS objects is not in the container of the
                current CUDS
            ValueError: Provided CUDS object is associated with the same
                session as the current CUDS object. Therefore, it is not an
                updated version.
            TypeError: Provided objects that are not of type CUDS as
                positional arguments.

        Returns:
            The CUDS objects that have been updated, associated with the
            session of the current CUDS object. Result type is a list,
            if more than one CUDS object is returned.
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
               *uids_or_cuds: Union["Cuds", UID],
               rel: Optional[OntologyRelationship] = cuba.activeRelationship,
               oclass: Optional[OntologyClass] = None) -> None:
        """Remove elements from the CUDS object.

        Expected calls are remove(), remove(*uids_or_cuds), remove(rel=___),
        remove(oclass=___), remove(*uids_or_cuds, rel=___),
        remove(rel=___, oclass=___).

        Args:
            uids_or_cuds: Optionally, specify the UIDs of the elements to
                remove or provide the elements themselves.
            rel: Only remove cuds_object which are connected by subclass of the
                given relationship. Defaults to cuba.activeRelationship. Can be
                set to none, in which case, all the contained elements will
                be removed.
            oclass: Only remove elements which are a subclass of the given
                ontology class. Defaults to None (no filter).

        Raises:
            RuntimeError: No CUDS object removed, because none of the
                specified CUDS objects are not in the container of the
                current CUDS object directly.
            TypeError: Incorrect argument types.
            ValueError: Both uids and an oclass passed to the function.
        """
        if uids_or_cuds and oclass is not None:
            raise ValueError("Do not specify both uids and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise TypeError("Found object of type %s passed to argument rel. "
                            "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError("Found object of type %s passed to argument "
                            "oclass. Should be an OntologyClass."
                            % type(oclass))
        check_arguments((UID, Cuds), *uids_or_cuds)

        self.session._notify_read(self)

        # Get mapping from uids to connecting relationships
        consider_relationships = set(self._neighbors)
        if rel:
            consider_relationships &= set(rel.subclasses)

        mapping = OrderedDict()
        for rel in consider_relationships:
            result_uids = self._iter(*uids_or_cuds, rel=rel, oclass=oclass,
                                     notify_read=False)
            if uids_or_cuds:
                result_uids = filter(None, result_uids)
            mapping.update(
                (uid, mapping.get(uid, set()) | {rel})
                for uid in result_uids
            )
        if not mapping:
            logger.warning("Did not remove any Cuds object, because none "
                           "matched your filter.")
            return

        neighbors = self._load_cuds_objects(mapping)
        for neighbor, relationships in zip(neighbors,
                                           mapping.values()):
            for relationship in relationships:
                self._remove_direct(relationship, neighbor.uid)
                neighbor._remove_inverse(relationship, self.uid)

    # ↑ ------ ↑
    # Public API

    @property
    def _neighbors(self):
        return NeighborDictRel(self)

    @property
    def _stored(self):
        return self.session is not None and self._graph is self.session.graph

    def get_triples(self, include_neighbor_types: bool = False):
        """Get the triples of the cuds object."""
        o_set = set()
        for s, p, o in self._graph.triples((self.iri, None, None)):
            yield s, p, o
            o_set.add(o)
        if include_neighbor_types:
            for o in o_set:
                yield from self._graph.triples((o, RDF.type, None))

    class _ObjectSet(DataStructureSet):
        """A set interface to an CUDS object's neighbors.

        This class looks like and acts like the standard `set`, but it
        is a template to implement classes that use either the attribute
        interface or the methods `_connect`, `_disconnect` and `_iter` from
        the CUDS object.

        When an instance is read or when it is modified in-place,
        the interfaced methods are used to reflect the changes.

        This class does not hold any object-related information itself, thus
        it is safe to spawn multiple instances linked to the same property
        and CUDS object (when single-threading).
        """
        _predicate: Optional[
            Union[OntologyAttribute, OntologyRelationship]]
        """Main predicate to which this object refers. It will be used
        whenever there is ambiguity on which predicate to use. Can be set to
        None, usually meaning all predicates (see the specific
        implementations of this class: `_AttributeSet` and
        `_RelationshipSet`)."""

        _individual: "Cuds"
        """The CUDS object to which this object is linked to. Whenever the set
        is modified, the modification will affect this CUDS object."""

        @property
        def cuds(self) -> "Cuds":
            """CUDS object that this set refers to."""
            return self._individual

        @property
        def predicate(self) -> Union[OntologyAttribute, OntologyRelationship]:
            """Predicate that this set refers to."""
            return self._predicate

        @property
        def _predicates(self) -> Optional[Union[
            Set[OntologyAttribute],
            Set[OntologyRelationship]
        ]]:
            """All the predicates to which this instance refers to.

            Returns:
                Such predicates, or none if no main predicate is
                associated with this `_ObjectSet`.
            """
            return self._predicate.subclasses \
                if self._predicate is not None else \
                None

        def __init__(self,
                     predicate: Optional[Union[OntologyAttribute,
                                               OntologyRelationship]],
                     individual: "Cuds"):
            """Fix the linked predicate and CUDS object."""
            self._individual = individual
            self._predicate = predicate
            super().__init__()

        def __repr__(self) -> str:
            """Return repr(self)."""
            return set(self).__repr__() \
                + ' <' \
                + (f'{self._predicate} ' if self._predicate is not None
                   else '') \
                + f'of CUDS object {self._individual}>'

        def one(self) -> Union["Cuds", RDFCompatibleType]:
            """Return one element.

            Return one element if the set contains one element, else raise
            an exception.

            Returns:
                The only element contained in the set.

            Raises:
                ResultEmptyError: No elements in the set.
                MultipleResultsError: More than one element in the set.
            """
            iter_self = iter(self)
            first_element = next(iter_self, StopIteration)
            if first_element is StopIteration:
                raise ResultEmptyError(f"No elements attached to "
                                       f"{self._individual} through "
                                       f"{self._predicate}.")
            second_element = next(iter_self, StopIteration)
            if second_element is not StopIteration:
                raise MultipleResultsError(f"More than one element attached "
                                           f"to {self._individual} through "
                                           f"{self._predicate}.")
            return first_element

        def any(self) -> Optional[Union["Cuds", RDFCompatibleType]]:
            """Return any element of the set.

            Returns:
                Any element from the set if the set is not empty, else None.
            """
            return next(iter(self), None)

        def all(self) -> "Cuds._ObjectSet":
            """Return all elements from the set.

            Returns:
                All elements from the set, namely the set itself.
            """
            return self

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

    @staticmethod
    def _attribute_modifier(func):
        """Decorator for functions that perform attribute modifications.

        To be used with `_add_attributes`, `_delete_attributes` and
        `_set_attributes` exclusively. The three functions are extremely
        similar. This decorator covers the code that they share.
        """
        @functools.wraps(func)
        def wrapper(self,
                    attribute: OntologyAttribute,
                    values: Iterable[RDFCompatibleType],
                    *args, **kwargs):
            values = set(values)
            for x in values:
                if not isinstance(x, RDF_COMPATIBLE_TYPES):
                    raise TypeError(f"Type '{type(x)}' of object {x} cannot "
                                    f"be set as attribute value, as it is "
                                    f"incompatible with the OWL standard")
            if self.session:
                self.session._notify_read(self)
            result = func(self, attribute, values, *args, **kwargs)
            if self.session:
                self.session._notify_update(self)
            return result
        return wrapper

    # Bind static method to use as decorator.
    _attribute_modifier = _attribute_modifier.__get__(object,
                                                      None)

    @_attribute_modifier
    def _add_attributes(self,
                        attribute: OntologyAttribute,
                        values: Set[RDFCompatibleType]):
        """Add values to a datatype property.

        If any of the values provided in `values` have already been assigned,
        then they are simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of objects whose types are compatible either
                with the OWL standard's data types for literals or compatible
                with OSP-core as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom data types are given
                (raised by decorator `_attribute_modifier`).
        """
        # TODO: prevent the end result having more than one value depending on
        #  ontology cardinality restrictions and/or functional property
        #  criteria.
        for value in values:
            self._graph.add((self.iri, attribute.iri,
                             Literal(attribute.convert_to_datatype(value),
                                     datatype=attribute.datatype)))

    @_attribute_modifier
    def _delete_attributes(self,
                           attribute: OntologyAttribute,
                           values: Set[RDFCompatibleType]):
        """Remove values from a datatype property.

        If any of the values provided in `values` are not present, they are
        simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of objects whose types are compatible either
                with the OWL standard's data types for literals or compatible
                with OSP-core as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom data types are given
                (raised by decorator `_attribute_modifier`).
        """
        for value in values:
            self._graph.remove((self.iri, attribute.iri,
                                Literal(attribute.convert_to_datatype(value),
                                        datatype=attribute.datatype)))

    @_attribute_modifier
    def _set_attributes(self,
                        attribute: OntologyAttribute,
                        values: Set[RDFCompatibleType]):
        """Replace values assigned to a datatype property.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of objects whose types are compatible either
                with the OWL standard's data types for literals or compatible
                with OSP-core as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom datatypes are given
                (raised by decorator `_attribute_modifier`).
        """
        # TODO: prevent the end result having more than one value depending on
        #  ontology cardinality restrictions and/or functional property
        #  criteria.
        self._graph.remove((self.iri, attribute.iri, None))
        for value in values:
            self._graph.add((self.iri, attribute.iri,
                             Literal(attribute.convert_to_datatype(value),
                                     datatype=attribute.datatype)))

    def _attribute_value_generator(self,
                                   attribute: OntologyAttribute,
                                   _notify_read: bool = True) \
            -> Iterator[RDFCompatibleType]:
        """Returns a generator of values assigned to the specified attribute.

        Args:
            attribute: The ontology attribute query for values.

        Returns:
            Generator that returns the attribute values.
        """
        # TODO (detach cuds from sessions): Workaround to keep the behavior:
        #  removed CUDS do not have attributes. Think of a better way to
        #  detach CUDS from sessions. `self._graph is not
        #  self.session.graph` happens when `session._notify_read` is called
        #  for this cuds, but this is hacky maybe not valid in general for
        #  all sessions.
        if self.session is None or\
                self._graph is not self.session.graph:
            raise AttributeError(f"The CUDS {self} does not belong to any "
                                 f"session. None of its attributes are "
                                 f"accessible.")

        if _notify_read:
            self.session._notify_read(self)
        for literal in self._graph.objects(self.iri, attribute.iri):
            # TODO: Recreating the literal to get a vector from
            #  literal.toPython() should not be necessary, find out why it
            #  is happening.
            literal = Literal(str(literal), datatype=literal.datatype,
                              lang=literal.language)
            yield literal.toPython()

    def _attribute_value_contains(self,
                                  attribute: OntologyAttribute,
                                  value: RDFCompatibleType,
                                  _notify_read: bool = True) \
            -> bool:
        """Whether a specific value is assigned to the specified attribute.

        Args:
            attribute: The ontology attribute query for values.

        Returns:
            Whether the specific value is assigned to the specified
            attribute or not.
        """
        # TODO (detach cuds from sessions): Workaround to keep the behavior:
        #  removed CUDS do not have attributes. Think of a better way to
        #  detach CUDS from sessions. `self._graph is not
        #  self.session.graph` happens when `session._notify_read` is called
        #  for this cuds, but this is hacky maybe not valid in general for
        #  all sessions.
        if self.session is None or\
                self._graph is not self.session.graph:
            raise AttributeError(f"The CUDS {self} does not belong to any "
                                 f"session. None of its attributes are "
                                 f"accessible.")

        if _notify_read:
            self.session._notify_read(self)

        if attribute.datatype in (None, RDF.langString):
            return any(str(value) == str(x)
                       for x in self._graph.objects(self.iri, attribute.iri)
                       if isinstance(x, Literal))
        else:
            literal = Literal(value, datatype=attribute.datatype)
            literal = Literal(str(literal), datatype=attribute.datatype)
            return literal in self._graph.objects(self.iri, attribute.iri)

    def _attribute_generator(self, _notify_read: bool = True) \
            -> Iterator[OntologyAttribute]:
        """Returns a generator of the attributes of this CUDS object.

        The generator only returns the OntologyAttribute objects, NOT the
        values.

        Returns:
            Generator that returns the attributes of this CUDS object.
        """
        # TODO (detach cuds from sessions): Workaround to keep the behavior:
        #  removed CUDS do not have attributes. Think of a better way to
        #  detach CUDS from sessions.
        if self.session is None or\
                self._graph is not self.session.graph:
            raise AttributeError(f"The CUDS {self} does not belong to any "
                                 f"session. None of its attributes are "
                                 f"accessible.")

        if _notify_read:
            self.session._notify_read(self)
        for predicate in self._graph.predicates(self.iri, None):
            obj = from_iri(predicate, raise_error=False)
            if isinstance(obj, OntologyAttribute):
                yield obj

    def _attribute_and_value_generator(self, _notify_read: bool = True) \
            -> Iterator[Tuple[OntologyAttribute,
                              Iterator[RDFCompatibleType]]]:
        """Returns a generator of both the attributes and their values.

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

    class _AttributeSet(_ObjectSet):
        """A set interface to a CUDS object's attributes.

        This class looks like and acts like the standard `set`, but it
        is an interface to the `_add_attributes`, _set_attributes`,
        `_delete_attributes`, `_attribute_value_contains` and
        `_attribute_value_generator` methods.

        When an instance is read, the methods `_attribute_value_generator`
        and `_attribute_value_contains` are used to fetch the data. When it
        is modified in-place, the methods `_add_attributes`, `_set_attributes`,
        and `_delete_attributes` are used to reflect the changes.

        This class does not hold any attribute-related information itself, thus
        it is safe to spawn multiple instances linked to the same attribute
        and CUDS (when single-threading).
        """
        _predicate: OntologyAttribute

        @property
        def _predicates(self) -> Set[OntologyAttribute]:
            """All the attributes to which this instance refers to.

            Returns:
                Such predicates are the subproperties of the main predicate, or
                if it is none, all the subproperties.
            """
            predicates = super()._predicates
            if predicates is None:
                predicates = set(
                    self._individual._attribute_generator(_notify_read=True))
                # The code below is technically true, but makes no
                #  difference due to how `_attribute_generator` is written.
                # predicates = set(itertools.chain(
                #    subclasses
                #    for attributes in
                #    self._individual._attribute_generator(_notify_read=True)
                #    for subclasses in attributes.subclasses
                # ))
            return predicates

        def __init__(self,
                     attribute: Optional[OntologyAttribute],
                     individual: "Cuds"):
            """Fix the liked OntologyAttribute and ontology individual."""
            super().__init__(attribute, individual)

        def __iter__(self) -> Iterator[RDFCompatibleType]:
            """The values assigned to the referred predicates.

            Such predicates are the main attribute and its subclasses.

            Returns:
                The mentioned values.
            """
            yielded: Set[RDFCompatibleType] = set()
            for value in itertools.chain(*(
                    self._individual._attribute_value_generator(
                        attribute=attribute)
                    for attribute in self._predicates
            )):
                if value not in yielded:
                    yielded.add(value)
                    yield value

        def __contains__(self, item: RDFCompatibleType) -> bool:
            """Check whether a value is assigned to the attribute."""
            return any(
                self._individual._attribute_value_contains(attribute, item)
                for attribute in self._predicates
            )

        def update(self, other: Iterable[RDFCompatibleType]) -> None:
            """Update the set with the union of itself and others."""
            underlying_set = set(self)
            added = set(other).difference(underlying_set)
            self._individual._add_attributes(self._predicate, added)

        def intersection_update(self, other: Iterable[RDFCompatibleType]) ->\
                None:
            """Update the set with the intersection of itself and another."""
            underlying_set = set(self)
            intersection = underlying_set.intersection(other)
            removed = underlying_set.difference(intersection)
            for attribute in self._predicates:
                self._individual._delete_attributes(attribute, removed)

        def difference_update(self, other: Iterable[RDFCompatibleType]) -> \
                None:
            """Remove all elements of another set from this set."""
            removed = set(self) & set(other)
            for attribute in self._predicates:
                self._individual._delete_attributes(attribute, removed)

        def symmetric_difference_update(self, other: Set[RDFCompatibleType])\
                -> None:
            """Update set with the symmetric difference of it and another."""
            underlying_set = set(self)
            symmetric_difference = underlying_set.symmetric_difference(other)
            added = symmetric_difference.difference(underlying_set)
            self._individual._add_attributes(self._predicate, added)
            removed = underlying_set.difference(symmetric_difference)
            for attribute in self._predicates:
                self._individual._delete_attributes(attribute,
                                                    removed)

    # ↑ -------------- ↑
    # Attribute handling

    # Relationship handling
    # ↓ ----------------- ↓

    def _connect(self,
                 *cuds_objects: "Cuds",
                 rel: OntologyRelationship) -> List["Cuds"]:
        """Connect CUDS objects to this one.

        Args:
            cuds_objects: The CUDS objects to connect.
            rel: The relationship to use.

        Returns:
            The connected CUDS objects, from the session to which this CUDS
            object belongs.

        Raises:
            ValueError: Connected a CUDS object that is already linked.
                Note: in fact, the exception raised is
                `ExistingCudsException`, but it is a subclass of `ValueError`.
        """
        check_arguments(Cuds, *cuds_objects)

        result = list()
        # update cuds objects if they are already in the session
        old_objects = self._session.load(
            *[cuds.uid for cuds in cuds_objects
              if cuds.session != self.session])
        for cuds in cuds_objects:
            # Recursively add the children to the registry
            if rel in self._neighbors \
                    and cuds.uid in self._neighbors[rel]:
                message = '{!r} is already in the container'
                raise self.ExistingCudsException(message.format(cuds))
            if self.session != cuds.session:
                cuds = self._recursive_store(cuds, next(old_objects))

            self._add_direct(cuds, rel)
            cuds._add_inverse(self, rel)
            result.append(cuds)
        return result

    def _disconnect(self,
                    *cuds_objects: Union["Cuds", UID],
                    rel: OntologyRelationship,
                    oclass: Optional[OntologyClass] = None) -> None:
        """Disconnect CUDS objects from this one.

        Args:
            cuds_objects: The CUDS objects to be disconnected. Can be left
                blank. Then all the connected CUDS are disconnected.
            rel: The ontology relationship that currently connects this
                object to such objects.
            oclass: Only disconnect CUDS objects belonging to this class.
        """
        uids = (c.uid if isinstance(c, Cuds) else c for c in cuds_objects)
        contained_uids = self._iter(*uids, rel=rel, oclass=oclass)
        contained_uids = filter(None, contained_uids)
        neighbors = self._load_cuds_objects(contained_uids)
        for neighbor in neighbors:
            self._remove_direct(rel, neighbor.uid)
            neighbor._remove_inverse(rel, self.uid)

    def _iter(self,
              *uids: Union["Cuds", UID],
              rel: OntologyRelationship,
              oclass: Optional[OntologyClass] = None,
              notify_read: bool = True) -> Union[
        Iterator[UID],
        Iterator[Optional[UID]],
    ]:
        """Iterate over the contained elements.

        Only iterate over objects with given uids, connected through a certain
        relationship and its sub-relationships and optionally filter by oclass.

        Expected calls are _iter(), _iter(rel=___), _iter(oclass=___),
        _iter(rel=___, oclass=___), _iter(*uids), _iter(*uids, rel=___).

        Args:
            uids: Filter the elements to be returned by their UIDs.
            rel: Only return CUDS objects connected with a subclass of
                relationship.
            oclass: Only return CUDS objects of a subclass of this ontology
                class. Defaults to None (no filter).
            notify_read: Whether to notify the session that this CUDS object
                was read. Defaults to True. An example of a situation
                where one could want to set it to False is, when the session is
                notified in advance and this function will be called several
                times within a loop. In this way, several useless
                `_notify_read` calls within the loop are avoided.

        Raises:
            ValueError: Wrong type of argument for `uids`.

        Returns:
            Calls without `*uids` (Iterator[UID]): The position of each
                element in the result is non-deterministic. This corresponds to
                the calls `_iter()`, `_iter(rel=___)`, `_iter(oclass=___)`,
                `_iter(rel=___, oclass=___)`.
            Calls with `uids` (Iterator[Optional[UID]]): The position of
                each element in the result is determined by the position of
                the corresponding UID in the given list of UIDs. In this
                case, the result can contain `None` values if a given UID is
                not a child of this CUDS object. This corresponds to the calls
                `_iter(*uids)`, `_iter(*uids, rel=___)`.
        """
        # TODO (detach cuds from sessions): Think of a better way to detach
        #  CUDS from sessions.
        # If Cuds are provided, convert them to UIDs.
        if uids:
            check_arguments((UID, Cuds), *uids)
        uids = [c.uid if isinstance(c, Cuds) else c for c in uids]

        if not self.session:
            yield from []
            return

        if notify_read:
            self.session._notify_read(self)
        collected_uid_dict = \
            OrderedDict(self._neighbors[rel]) if not uids else \
            OrderedDict((uid, self._neighbors[rel][uid])
                        if uid in self._neighbors[rel] else (uid, None)
                        for uid in uids)

        if oclass is not None:
            collected_uid_dict = OrderedDict(
                (key, target_classes)
                if any(t.is_subclass_of(oclass) for t in target_classes)
                else (key, None)
                for key, target_classes in collected_uid_dict.items()
            )
            if not uids:
                collected_uid_dict = OrderedDict(
                    (key, target_classes)
                    for key, target_classes in collected_uid_dict.items()
                    if target_classes is not None
                )
        collected_uids = (uid if target is not None else None
                          for uid, target in collected_uid_dict.items())
        yield from collected_uids

    class _RelationshipSet(_ObjectSet):
        """A set interface to an CUDS object's relationships.

        This class looks like and acts like the standard `set`, but it
        is an interface to the `_connect`, `_disconnect` and `_iter` methods.

        When an instance is read, the method `_iter` is used to fetch the
        data. When it is modified in-place, the methods `_connect` and
        `_disconnect` are used to reflect the changes.

        This class does not hold any relationship-related information itself,
        thus it is safe to spawn multiple instances linked to the same
        relationship and CUDS object (when single-threading).
        """
        _predicate: Optional[OntologyRelationship]
        _class_filter: Optional[OntologyClass]

        def __init__(self,
                     relationship: Optional[OntologyRelationship],
                     individual: 'Cuds',
                     oclass: Optional[OntologyClass] = None):
            """Fix the liked OntologyRelationship and ontology individual."""
            if relationship is not None \
                    and not isinstance(relationship, OntologyRelationship):
                raise ValueError("Found object of type %s. "
                                 "Should be an OntologyRelationship."
                                 % type(relationship))
            if oclass is not None and not isinstance(oclass, OntologyClass):
                raise ValueError("Found object of type %s oclass. Should be "
                                 "an OntologyClass."
                                 % type(oclass))
            self._class_filter = oclass
            super().__init__(relationship, individual)

        def __iter__(self) -> Iterator['Cuds']:
            """The CUDS assigned to relationship`self._predicate`.

            Returns:
                The mentioned underlying set.
            """
            yielded: Set[Cuds] = set()
            predicates = self._predicates
            predicates = set(self._individual._neighbors) \
                if self._predicates is None else \
                predicates & set(self._individual._neighbors)
            for value in itertools.chain(*(
                    self._individual._load_cuds_objects(
                    self._individual._iter(rel=predicate,
                                           oclass=self._class_filter)
                    )
                    for predicate in predicates
            )):
                if value not in yielded:
                    yielded.add(value)
                    yield value

        def __contains__(self, item) -> bool:
            """Check if an individual is connected via the relationship."""
            predicates = self._predicates
            predicates = set(self._individual._neighbors) \
                if self._predicates is None else \
                predicates & set(self._individual._neighbors)
            return any(predicate in self._individual._neighbors
                       and item.uid in self._individual._neighbors[predicate]
                       and (item.is_a(self._class_filter)
                            if self._class_filter is not None else
                            True)
                       for predicate in predicates)

        @staticmethod
        def prevent_class_filtering(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                if self._class_filter is not None:
                    raise RuntimeError("Cannot edit a set with a class "
                                       "filter in-place.")
                return func(self, *args, **kwargs)
            return wrapper

        # Bind static method to use as decorator.
        prevent_class_filtering = prevent_class_filtering.__get__(object,
                                                                  None)

        @prevent_class_filtering
        def update(self, other: Iterable['Cuds']) -> None:
            """Update the set with the union of itself and other."""
            # The individuals to update might be already attached. Given an
            #  individual from `other`, several situations may arise:
            #
            #    1 - The relationship through which it is already attached is
            #        the same as the main predicate `self._predicate`. It is
            #        safe to attach it again, the same connection cannot be
            #        duplicated in the RDF standard.
            #
            #    2 - The relationship through which it is already attached is a
            #        sub-relationship of the main predicate. In such case,
            #        we keep the existing connection and do not add a new
            #        connection. The principle is: the more specific the
            #        knowledge is, the better.
            #
            #    3 - The relationship through which it is already attached is a
            #        super-relationship of the main predicate. Then it can make
            #        sense to remove the original connection and replace it
            #        with a new, more specific connection using the main
            #        predicate.
            #
            added = filter(lambda x: x not in self, other)  # Takes care of 2.
            # TODO: We do not take care of 3, because `.add` also does not
            #  take care of 3. This topic can be an object of discussion.
            for individual in added:
                self._individual._connect(individual, rel=self._predicate)

        @prevent_class_filtering
        def intersection_update(self, other: Iterable['Cuds'])\
                -> None:
            """Update the set with the intersection of itself and another."""
            # Note: please read the comment on the `update` method.
            underlying_set = set(self)
            result = underlying_set.intersection(other)

            removed = underlying_set.difference(result)
            if removed:
                for rel in self._predicates:
                    self._individual._disconnect(*removed, rel=rel)

            added = result.difference(underlying_set)
            self._individual._connect(*added, rel=self._predicate)

        @prevent_class_filtering
        def difference_update(self, other: Iterable['Cuds']) \
                -> None:
            """Remove all elements of another set from this set."""
            # Note: please read the comment on the `update` method.
            removed = set(self) & set(other)
            if removed:
                for rel in self._predicates:
                    self._individual._disconnect(*removed, rel=rel)

        @prevent_class_filtering
        def symmetric_difference_update(self,
                                        other: Iterable['Cuds'])\
                -> None:
            """Update with the symmetric difference of it and another."""
            # Note: please read the comment on the `update` method.
            underlying_set = set(self)
            result = underlying_set.symmetric_difference(other)

            removed = underlying_set.difference(result)
            if removed:
                for rel in self._predicates:
                    self._individual._disconnect(*removed, rel=rel)

            added = result.difference(underlying_set)
            self._individual._connect(*added, rel=self._predicate)

    # ↑ -------------- ↑
    # Relationship handling

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
    def _fix_old_neighbors(new_cuds_object: 'Cuds',
                           old_cuds_object: Optional['Cuds'],
                           old_neighbors: Iterable['Cuds'],
                           old_neighbor_diff: Iterable[
                               Tuple[UID, OntologyRelationship]]):
        """Fix the relationships of the added Cuds objects.

        Fixes relationships to Cuds object that were previously neighbors.

        Args:
            new_cuds_object: The added Cuds object
            old_cuds_object: The Cuds object that is going
                to be replaced
            old_neighbors: The Cuds object that were neighbors
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

    def _add_direct(self, cuds_object: 'Cuds', rel: OntologyRelationship):
        """Add an cuds_object with a specific relationship.

        Args:
            cuds_object: CUDS object to be added
            rel: relationship with the cuds_object to add.
        """
        # First element, create set
        if rel not in self._neighbors:
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

    def _load_cuds_objects(self, uids: Iterable[UID]) -> Iterator['Cuds']:
        """Load the cuds_objects of the given uids from the session.

        Each in cuds_object is at the same position in the result as
        the corresponding uid in the given uid list.
        If the given uids contain None values, there will be
        None values at the same position in the result.

        Args:
            uids: The uids to fetch from the session.

        Yields:
            Generator of loaded cuds_objects.
        """
        # TODO: Think of a better way to detach CUDS from sessions.
        if not self.session:
            return None

        uids = list(uids)
        without_none = list(filter(None, uids))
        cuds_objects = self.session.load(*without_none)
        for uid in uids:
            if uid is None:
                yield None
            else:
                try:
                    yield next(cuds_objects)
                except StopIteration:
                    return None

    def _remove_direct(self, relationship: OntologyRelationship, uid: UID):
        """Remove the direct relationship to the object with given uid.

        Args:
            relationship: The relationship to remove.
            uid: The uid to remove.
        """
        del self._neighbors[relationship][uid]
        if not self._neighbors[relationship]:
            del self._neighbors[relationship]

    def _remove_inverse(self, relationship: OntologyRelationship, uid: UID):
        """Remove the inverse of the given relationship.

        Args:
            relationship: The relationship to remove.
            uid: The uid to remove.
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
