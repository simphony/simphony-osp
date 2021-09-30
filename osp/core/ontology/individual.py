"""An ontology individual."""

import itertools
import logging
from abc import ABC, abstractmethod
from typing import (Any, Dict, Iterable, Iterator, List, MutableSet, Optional,
                    Set, TYPE_CHECKING, Tuple, Union)

from rdflib import RDF, Literal

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.datatypes import (UID, RDFCompatibleType,
                                         RDF_COMPATIBLE_TYPES, Triple)
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.relationship import OntologyRelationship

if TYPE_CHECKING:
    from osp.core.ontology.oclass import OntologyClass
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class OntologyIndividual(OntologyEntity):
    """An ontology individual."""

    # Public API
    # ↓ ------ ↓

    @property
    def oclass(self) -> Optional['OntologyClass']:
        """Get the ontology class of the ontology individual.

        Returns:
            The ontology class of the ontology individual. If the individual
            belongs to multiple classes, then ONLY ONE of them is returned.
            When the ontology individual does not belong to any ontology class.
        """
        oclasses = self.oclasses
        return oclasses[0] if oclasses else None

    @property
    def oclasses(self) -> Tuple['OntologyClass']:
        """Get the ontology classes of this ontology individual.

        Returns:
            A tuple with all the ontology classes of the ontology
            individual. When the individual has no classes, the tuple is empty.
        """
        # TODO: Why only from `tbox`? Think of assigning a specific ontology
        #  as TBox to a session for example.
        return tuple(self.session.from_identifier(o)
                     for o in self.session.graph.objects(self.identifier,
                                                         RDF.type))

    def is_a(self, oclass: 'OntologyClass') -> bool:
        """Check if the individual is an instance of the given ontology class.

        Args:
            oclass: The ontology class to test against.

        Returns:
            Whether the ontology individual is an instance of such ontology
                class.
        """
        return any(oc in oclass.subclasses for oc in self.oclasses)

    def add(self,
            *individuals: 'OntologyIndividual',
            rel: Optional[OntologyRelationship] = None) -> \
            Union['OntologyIndividual', List['OntologyIndividual']]:
        if rel is None:
            from osp.core.namespaces import cuba
            rel = cuba.activeRelationship
        individuals_set = set(individuals)
        existing_set = set(self._iter(rel=rel))
        individuals_in_this_session = set()
        for individual in individuals_set.difference(existing_set):
            self._connect(individual, rel=rel)
            individuals_in_this_session.add(
                self.session.from_identifier(individual.identifier))
        return individuals_in_this_session.pop() \
            if len(individuals_in_this_session) == 1 else \
            list(individuals_in_this_session)

    def remove(self,
               *args: Union[UID, 'OntologyIndividual'],
               rel: Optional[OntologyRelationship] = None,
               oclass: 'OntologyClass' = None) -> \
            Optional[Union['OntologyIndividual',
                           List['OntologyIndividual']]]:
        if rel is None:
            from osp.core.namespaces import cuba
            rel = cuba.activeRelationship
        args = set(arg.uid if isinstance(arg, OntologyIndividual) else arg
                   for arg in args)
        individuals_and_relationships = filter(
            lambda x: x[0].uid in args if args else True,
            self._iter(rel=rel, oclass=oclass, return_rel=True))
        for individual, relationship in individuals_and_relationships:
            self._disconnect(individual, rel=relationship)

    def get(self,
            *uids: UID,
            rel: Optional[OntologyRelationship] = None,
            oclass: 'OntologyClass' = None) -> \
            Optional[Union['OntologyIndividual', List['OntologyIndividual']]]:
        if rel is None:
            from osp.core.namespaces import cuba
            rel = cuba.activeRelationship
        result = list(filter(lambda x: x.uid in uids if uids else True,
                             self._iter(rel=rel, oclass=oclass)))
        return result.pop() if len(uids) == 1 else result

    def iter(self,
            *uids: UID,
            rel: Optional[OntologyRelationship] = None,
            oclass: 'OntologyClass' = None) -> \
            Optional[Union['OntologyIndividual', List['OntologyIndividual']]]:
        if rel is None:
            from osp.core.namespaces import cuba
            rel = cuba.activeRelationship
        yield from filter(lambda x: x.uid in uids if uids else True,
                          self._iter(rel=rel, oclass=oclass))

    def __dir__(self) -> Iterable[str]:
        """Show the individual's attributes as autocompletion suggestions."""
        result = iter(())
        attributes_and_namespaces = (
            (attr, ns)
            for oclass in self.oclasses
            for attr in oclass.attribute_declaration.keys()
            for ns in attr.session.namespaces
            if attr in ns
        )
        for attribute, namespace in attributes_and_namespaces:
            if namespace.reference_style:
                result = itertools.chain(
                    result,
                    attribute.iter_labels(return_literal=False)
                )
            else:
                result = itertools.chain(
                    result,
                    (attribute.iri[len(namespace.iri):], )
                )
        return itertools.chain(super().__dir__(), result)

    def __getattr__(self, name: str) -> RDFCompatibleType:
        """Retrieve an attribute whose domain matches the individual's oclass.

        Args:
            name: The name of the attribute.

        Raises:
            AttributeError: Unknown attribute name.

        Returns:
            The value of the attribute (a python object).
        """
        # TODO: The current behavior is to fail with non functional attributes.
        #  However, the check is based on the amount of values set for an
        #  attribute and not its definition as functional or non-functional
        #  in the ontology.
        # TODO: If an attribute whose domain is not explicitly specified was
        #  already fixed with __setitem__, then this should also give back
        #  such attributes.
        attr = self._get_ontology_attribute_by_name(name)
        values = self._attribute_value_generator(attr)
        value = next(values, None)
        if next(values, None) is not None:
            raise RuntimeError(f"Tried to fetch values of a "
                               f"non-functional attribute {attr} using "
                               f"the dot notation. This is not "
                               f"supported. "
                               f"\n \n"
                               f"Please use subscript "
                               f"notation instead for such attributes: "
                               f"my_cuds[{attr}]. This will return a set "
                               f"of values instead of a single one")
        return value

    def __setattr__(self, name: str,
                    value: Union[RDFCompatibleType,
                                 Set[RDFCompatibleType]]) -> None:
        """Set the value(s) of an attribute.

        Args:
            name: The name of the attribute.
            value: The new value(s).

        Raises:
            AttributeError: Unknown attribute name.
        """
        # TODO: prohibit assignment of multiple values to functional
        #  attributes and/or attributes with cardinality constraints that
        #  forbid more than one value.
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        try:
            attr = self._get_ontology_attribute_by_name(name)
            value = {value} \
                if not isinstance(value, (Set, MutableSet)) \
                else value
            # Apparently instances of MutableSet are not instances of Set.
            self._set_attributes(attr, value)
        except AttributeError as e:
            # Might still be an attribute of a subclass of OntologyIndividual.
            if hasattr(self, name):
                super().__setattr__(name, value)
            else:
                raise e

    def __getitem__(self,
                    value: Union['OntologyAttribute', 'OntologyRelationship',
                                 Tuple[
                                     Union['OntologyAttribute',
                                           'OntologyRelationship'],
                                     slice]]) \
            -> Optional[
                Union['OntologyIndividual._AttributeSet',
                      'OntologyIndividual._RelationshipSet',
                      'OntologyIndividual',
                      RDFCompatibleType]]:
        """Retrieve linked ontology individuals or attribute values.

        The subscripting syntax `individual[rel]` allows:
        - When `rel` is an OntologyAttribute, to obtain ONLY ONE
          (non-deterministic) value of such attribute.
        - When `rel` is an OntologyRelationship, to obtain ONLY ONE
          (non-deterministic) ontology individual of all the ontology
          individuals linked to `individual` through the `rel` relationship.

        The subscripting syntax `individual[rel, :]` allows:
        - When `rel` is an OntologyAttribute, to obtain a set containing all
          the values assigned to the specified attribute. Such set can be
          modified in-place to change the assigned values.
        - When `rel` is an OntologyRelationship, to obtain a set containing
          all CUDS objects that are connected to `individual` through rel.
          Such set can be modified in-place to modify the existing connections.

        The reason why a set is returned and not a list, or any other
        container allowing repeated elements, is that the underlying RDF
        graph does not accept duplicate statements.

        Args:
            value: Two possibilities,
                - Just an ontology attribute or an ontology relationship
                  (OWL datatype property, OWL object property). Then only one
                  CUDS object or attribute value is returned.
                - A tuple (multiple keys specified). The first element of the
                  tuple is expected to be such attribute or relationship, and
                  the second a `slice` object. When `slice(None, None, None)`
                  (equivalent to `:`) is provided, a set-like object of
                  values is returned. This is the the only kind of slice
                  supported.

        Raises:
            TypeError: Trying to use something that is neither an
                OntologyAttribute or an OntologyRelationship as index.
            IndexError: When invalid slicing is provided.
        """
        if isinstance(value, tuple):
            rel, slicing = value
        else:
            rel, slicing = value, None

        if isinstance(rel, OntologyAttribute):
            class_ = self._AttributeSet
        elif isinstance(rel, OntologyRelationship):
            class_ = self._RelationshipSet
        else:
            raise TypeError(f'Ontology individual indices must be ontology '
                            f'relationships or ontology attributes, '
                            f'not {type(rel)}')

        if slicing is None:
            try:
                return set(class_(rel, self)).pop()
            except KeyError:
                return None
        elif slicing == slice(None, None, None):
            return class_(rel, self)
        elif not isinstance(slicing, slice):
            raise IndexError(f"Invalid slicing {slicing}.")
        else:
            raise IndexError(
                f'Invalid index [{rel}, '
                f'{slicing.start if slicing.start is not None else ""}:'
                f'{slicing.stop if slicing.stop is not None else ""}'
                f'{":" if slicing.step is not None else ""}'
                f'{slicing.step if slicing.step is not None else ""}'
                f']. \n'
                f'Only slicing of the kind [{rel}, :], or no slicing, '
                f'i.e. [{rel}] is supported.')

    def __setitem__(self,
                    rel: Union[OntologyAttribute, 'OntologyRelationship'],
                    values: Optional[Union[
                        Union['OntologyIndividual', RDFCompatibleType],
                        Set[Union['OntologyIndividual', RDFCompatibleType]]]],
                    ) -> None:
        """Manages both individuals object properties and data properties.

        The subscripting syntax `individual[rel] = ` allows,

        - when `rel` is an OntologyRelationship, to replace the list of
          ontology individuals that are connected to `individual` through rel,
        - and when `rel` is an OntologyAttribute, to replace the values of
          such attribute.

        The subscripting syntax `individual[rel, :] = `, even though not
        considered on the type hints is also accepted. However, but the effect
        it produces is the same. It is nevertheless required with in-place
        operators such as `+=` or `&=` if one wants to operate on the set of
        attributes values rather than on the attribute. See the docstring of
        `__getitem__` for more details.

        This function only accepts hashable objects as input, as the
        underlying RDF graph does not accept duplicate statements.

        Args:
            rel: Either an ontology attribute or an ontology relationship
                (OWL datatype property, OWL object property).
            values: Either a single element compatible with the OWL standard
                (this includes ontology individuals objects) or a set of such
                elements.

        Raises:
            TypeError: Trying to assign attributes using an object property,
                trying to assign ontology individuals using a data property,
                trying to use something that is neither an OntologyAttribute
                or an OntologyRelationship as index.
        """
        if isinstance(rel, tuple) and rel[1] == slice(None, None, None):
            rel = rel[0]
        values = values or set()
        values = {values} \
            if not isinstance(values, (Set, MutableSet)) \
            else values
        # Apparently instances of MutableSet are not instances of Set.
        # TODO: Check arguments.
        # TODO: validating data types first and then splitting by data types
        #  sounds like redundancy and decrease in performance.
        # check_arguments((Cuds, *RDF_COMPATIBLE_TYPES), *values)
        individuals, literals = \
            tuple(
                filter(lambda x: isinstance(x, OntologyIndividual), values)), \
            tuple(
                filter(lambda x: isinstance(x, RDF_COMPATIBLE_TYPES), values))

        if isinstance(rel, OntologyRelationship):
            if len(literals) > 0:
                raise TypeError(f'Trying to assign attributes using an object '
                                f'property {rel}.')
        elif isinstance(rel, OntologyAttribute):
            if len(individuals) > 0:
                raise TypeError(f'Trying to connect ontology individuals '
                                f'using a data property {rel}.')

        if isinstance(rel, OntologyRelationship):
            individuals_set = set(individuals)
            existing_set = set(self._iter(rel=rel))

            to_connect = individuals_set.difference(existing_set)
            for individual in to_connect:
                self._connect(individual, rel=rel)

            to_disconnect = existing_set.difference(individuals_set)
            for individual in to_disconnect:
                self._disconnect(individual, rel=rel)
        elif isinstance(rel, OntologyAttribute):
            self._set_attributes(rel, literals)
        else:
            raise TypeError(f'Ontology individual indices must be ontology '
                            f'relationships or ontology attributes, '
                            f'not {type(rel)}.')

    def __delitem__(self, rel: Union[OntologyAttribute, OntologyRelationship]):
        """Delete all attributes or data properties attached through rel.

        Args:
            rel: Either an ontology attribute or an ontology relationship
                (OWL datatype property, OWL object property).
        """
        self.__setitem__(rel=rel, values=set())

    # ↑ ------ ↑
    # Public API

    class _ObjectSet(MutableSet, ABC):
        """A set interface to an ontology individual's neighbors.

        This class looks like and acts like the standard `set`, but it
        is a template to implement classes that use either the attribute
        interface or the methods `_connect`, `_disconnect` and `_iter` from
        the ontology individual.

        When an instance is read or when it is modified in-place,
        the interfaced methods are used to reflect the changes.

        This class does not hold any object-related information itself, thus
        it is safe to spawn multiple instances linked to the same property
        and ontology individual (when single-threading).
        """
        _predicate: Union[OntologyAttribute, OntologyRelationship]
        _individual: "OntologyIndividual"

        def __init__(self,
                     predicate: Union[OntologyAttribute,
                                      OntologyRelationship],
                     individual: "OntologyIndividual"):
            """Fix the liked property and CUDS object."""
            self._individual = individual
            self._predicate = predicate
            super().__init__()

        @property
        @abstractmethod
        def _underlying_set(self) -> Set:
            """The set of values assigned to the property `self._property`.

            Returns:
                The mentioned underlying set.
            """
            pass

        def __repr__(self) -> str:
            """Return repr(self)."""
            return self._underlying_set.__repr__() \
                + f' <{self._predicate} of ontology individual ' \
                  f'{self._individual}>'

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

        @abstractmethod
        def __len__(self) -> int:
            """Return len(self)."""
            pass

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

        def __and__(self, other: set) -> Union[Set[RDFCompatibleType],
                                               Set["OntologyIndividual"]]:
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

        @abstractmethod
        def __ior__(self, other: Union[Set[RDFCompatibleType],
                                       Set["OntologyIndividual"]]):
            """Return self|=other."""
            pass

        @abstractmethod
        def __iand__(self, other: Union[Set[RDFCompatibleType],
                                        Set["OntologyIndividual"]]):
            """Return self&=other."""
            pass

        @abstractmethod
        def __ixor__(self, other: Union[Set[RDFCompatibleType],
                                        Set["OntologyIndividual"]]):
            """Return self^=other."""
            pass

        def __iadd__(self, other: Set[RDFCompatibleType]):
            """Return self+=other (equivalent to self|=other)."""
            if isinstance(other, (Set, MutableSet)):
                # Apparently instances of MutableSet are not instances of Set.
                return self.__ior__(other)
            else:
                return self.__ior__({other})

        @abstractmethod
        def __isub__(self, other: Any):
            """Return self-=other."""
            pass

        def isdisjoint(self, other: set):
            """Return True if two sets have a null intersection."""
            return self._underlying_set.isdisjoint(other)

        @abstractmethod
        def clear(self):
            """Remove all elements from this set.

            This also removes all the values assigned to the property
            linked to this set for the cuds linked to this set.
            """
            pass

        @abstractmethod
        def pop(self) -> Union[RDFCompatibleType, "OntologyIndividual"]:
            """Remove and return an arbitrary set element.

            Raises KeyError if the set is empty.
            """
            pass

        def copy(self):
            """Return a shallow copy of a set."""
            return self._underlying_set

        def difference(self, other: Iterable) -> Union[
                Set[RDFCompatibleType], Set["OntologyIndividual"]]:
            """Return the difference of two or more sets as a new set.

            (i.e. all elements that are in this set but not the others.)
            """
            return self._underlying_set.difference(other)

        @abstractmethod
        def difference_update(self, other: Iterable):
            """Remove all elements of another set from this set."""
            pass

        @abstractmethod
        def discard(self, other: Any):
            """Remove an element from a set if it is a member.

            If the element is not a member, do nothing.
            """
            pass

        @abstractmethod
        def intersection(self, other: set) -> Union[Set[RDFCompatibleType],
                                                    Set["OntologyIndividual"]]:
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

        def add(self, other: Union[RDFCompatibleType, "OntologyIndividual"]):
            """Add an element to a set.

            This has no effect if the element is already present.
            """
            self.__ior__({other})

        @abstractmethod
        def remove(self, other: Any):
            """Remove an element from a set; it must be a member.

            If the element is not a member, raise a KeyError.
            """
            pass

        @abstractmethod
        def update(self, other: Iterable):
            """Update a set with the union of itself and others."""
            pass

    def _get_direct_superclasses(self) -> Iterable['OntologyEntity']:
        return (x for oclass in self.oclasses
                for x in oclass.direct_superclasses)

    def _get_direct_subclasses(self) -> Iterable['OntologyEntity']:
        return (x for oclass in self.oclasses
                for x in oclass.direct_subclasses)

    def _get_superclasses(self) -> Iterable['OntologyEntity']:
        return (x for oclass in self.oclasses
                for x in oclass.superclasses)

    def _get_subclasses(self) -> Iterable['OntologyEntity']:
        return (x for oclass in self.oclasses
                for x in oclass.subclasses)

    # Relationship handling
    # ↓ ----------------- ↓

    def _connect(self,
                 other: "OntologyIndividual",
                 rel: OntologyRelationship) -> \
            'OntologyIndividual':
        """Connect an ontology individual to this one.

        If the connected object is associated with the same session, only a
        link is created. Otherwise, the information associated with the
        connected object is added to the session of this ontology individual.

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
        if other.triples:
            self.session.store(other)
        self.session.graph.add(
            (self.identifier, rel.identifier, other.identifier))
        return self.session.from_identifier(other.identifier)

    def _disconnect(self,
                    other: Optional["OntologyIndividual"] = None,
                    rel: Optional[OntologyRelationship] = None):
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
        self.session.graph.remove(
            (self.identifier,
             rel.identifier if rel is not None else None,
             other.identifier if other is not None else None))

    def _iter(self,
              rel: Optional[OntologyRelationship] = None,
              oclass: Optional['OntologyClass'] = None,
              return_rel: bool = False) \
            -> Iterator["OntologyIndividual"]:
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
            uids: uids of the elements.
            rel: Only return cuds_object which are connected by subclass of
                given relationship. Defaults to cuba.activeRelationship.
            oclass: Only return elements which are a
                subclass of the given ontology class. Defaults to None.
            return_rel: Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Iterator[Cuds]: The queried objects.
        """
        if rel is None:
            from osp.core.namespaces import cuba
            rel = cuba.activeRelationship

        entities_and_relationships = (
            (self.session.from_identifier(x), sub)
            for sub in rel.subclasses
            for x in self.session.graph.objects(self.identifier,
                                                sub.identifier))
        if oclass:
            entities_and_relationships = (
                (entity, relationship)
                for entity, relationship in entities_and_relationships
                if oclass in entity.superclasses)

        if return_rel:
            yield from entities_and_relationships
        else:
            yield from map(lambda x: x[0], entities_and_relationships)

    class _RelationshipSet(_ObjectSet, MutableSet):
        """A set interface to a CUDS object's RELATIONSHIPS.

        This class looks like and acts like the standard `set`, but it
        is an interface to the `add`, `get` and `remove` methods.

        When an instance is read, the method `get` is
        used to fetch the data. When it is modified in-place, the methods
        `add` and `remove` are used to reflect the changes.

        This class does not hold any relationship-related information itself,
        thus it is safe to spawn multiple instances linked to the same
        relationship and CUDS (when single-threading).
        """
        _predicate: OntologyRelationship
        _individual: "OntologyIndividual"

        @property
        def _underlying_set(self) -> Set["OntologyIndividual"]:
            """The set of values assigned to the attribute `self._predicate`.

            Returns:
                The mentioned underlying set.
            """
            return set(self._individual._iter(rel=self._predicate))

        def __init__(self,
                     relationship: OntologyRelationship,
                     individual: "OntologyIndividual"):
            """Fix the liked OntologyAttribute and CUDS object."""
            super().__init__(relationship, individual)

        def __len__(self) -> int:
            """Return len(self)."""
            i = 0
            for x in self._individual._iter(rel=self._predicate):
                i += 1
            return i

        def __and__(self, other: set) -> Set['OntologyIndividual']:
            """Return self&other."""
            return super().__and__(other)

        def __ior__(self, other: Set['OntologyIndividual']):
            """Return self|=other."""
            # TODO: Avoid the for loop by finding a way to roll back the
            #  added CUDS?
            for individual in other:
                self._individual._connect(individual, rel=self._predicate)
            return self

        def __iand__(self, other: Set["OntologyIndividual"]):
            """Return self&=other."""
            underlying_set = self._underlying_set
            intersection = underlying_set.intersection(other)
            removed = underlying_set.difference(intersection)
            for individual in removed:
                self._individual._disconnect(individual, rel=self._predicate)
            return self

        def __ixor__(self, other: Set["OntologyIndividual"]):
            """Return self^=other."""
            result = self._underlying_set ^ other
            to_add = result.difference(self._underlying_set)
            to_remove = self._underlying_set.difference(result)
            for individual in to_remove:
                self._individual._disconnect(individual, rel=self._predicate)
            for individual in to_add:
                self._individual._connect(individual, rel=self._predicate)
            return self

        def __isub__(self, other: Any):
            """Return self-=other."""
            if isinstance(other, (Set, MutableSet)):
                # Apparently instances of MutableSet are not instances of Set.
                to_remove = self._underlying_set & set(other)
            else:
                to_remove = self._underlying_set & {other}
            for individual in to_remove:
                self._individual._disconnect(individual, rel=self._predicate)
            return self

        def clear(self):
            """Remove all elements from this set.

            This also removed all the values assigned to the attribute
            linked to this set for the cuds linked to this set.
            """
            self._individual._disconnect(None, rel=self._predicate)

        def pop(self) -> "OntologyIndividual":
            """Remove and return an arbitrary set element.

            Raises KeyError if the set is empty.
            """
            result = self._underlying_set.pop()
            self._individual._disconnect(result, rel=self._predicate)
            return result

        def difference(self, other: Iterable) -> Set["OntologyIndividual"]:
            """Return the difference of two or more sets as a new set.

            (i.e. all elements that are in this set but not the others.)
            """
            return super().difference(other)

        def difference_update(self, other: Iterable):
            """Remove all elements of another set from this set."""
            to_remove = self._underlying_set.intersection(other)
            for individual in to_remove:
                self._individual._disconnect(individual, rel=self._predicate)

        def discard(self, other: Any):
            """Remove an element from a set if it is a member.

            If the element is not a member, do nothing.
            """
            self._individual._disconnect(other, rel=self._predicate)

        def intersection(self, other: set) -> Set["OntologyIndividual"]:
            """Return the intersection of two sets as a new set.

            (i.e. all elements that are in both sets.)
            """
            return super().intersection(other)

        def add(self, other: "OntologyIndividual"):
            """Add an element to a set.

            This has no effect if the element is already present.
            """
            return super().add(other)

        def remove(self, other: Any):
            """Remove an element from a set; it must be a member.

            If the element is not a member, raise a KeyError.
            """
            to_remove = self._underlying_set & other
            for individual in to_remove:
                self._individual._disconnect(individual, rel=self._predicate)
            else:
                raise KeyError(f"{other}")

        def update(self, other: Iterable):
            """Update a set with the union of itself and others."""
            self.__ior__(set(other))

    # ↑ ----------------- ↑
    # Relationship handling

    # Attribute handling
    # ↓ -------------- ↓

    def get_attributes(self) -> Dict[OntologyAttribute,
                                     Set[RDFCompatibleType]]:
        """Get the attributes as a dictionary."""
        return {attribute: set(value_generator)
                for attribute, value_generator
                in self._attribute_and_value_generator()}

    def _get_ontology_attribute_by_name(self, name: str) -> OntologyAttribute:
        """Get an ontology attribute of this individual by name."""
        attributes_and_reference_styles = (
            (attr, ns.reference_style)
            for oclass in self.oclasses
            for attr in oclass.attribute_declaration.keys()
            for ns in attr.session.namespaces
            if attr in ns
        )
        for attr, reference_style in attributes_and_reference_styles:
            if any((
                    reference_style
                    and name in attr.iter_labels(return_literal=False),
                    not reference_style and str(attr.identifier).endswith(name)
            )):
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
            values: An iterable of Python types that are compatible either
                with the OWL standard's data types for literals or compatible
                with OSP-core as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom data types are given.
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

        for value in values:
            self.session.graph.add(
                (self.iri, attribute.iri,
                 Literal(attribute.convert_to_datatype(value),
                         datatype=attribute.datatype)))

    def _delete_attributes(self,
                           attribute: OntologyAttribute,
                           values: Iterable[RDFCompatibleType]):
        """Remove values from a datatype property.

        If any of the values provided in `values` are not present, they are
        simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of Python types that are compatible either
                with the OWL standard's data types for literals or compatible
                with OSP-core as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with OSP-core as custom data types are given.
        """
        values = set(values)
        for x in values:
            if not isinstance(x, RDF_COMPATIBLE_TYPES):
                logger.warning(f"Type '{type(x)}' of object {x} cannot "
                               f"be an attribute value, as it is "
                               f"incompatible with the OWL standard")

        for value in values:
            self.session.graph.remove(
                (self.iri, attribute.iri,
                 Literal(attribute.convert_to_datatype(value),
                         datatype=attribute.datatype)))

    def _set_attributes(self,
                        attribute: OntologyAttribute,
                        values: Iterable[RDFCompatibleType]):
        """Replace values assigned to a datatype property.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of Python types that are compatible either
                with the OWL standard's data types for literals or compatible
                with OSP-core as custom data types.

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

        self.session.graph.remove((self.iri, attribute.iri, None))
        for value in values:
            self.session.graph.add(
                (self.iri, attribute.iri,
                 Literal(attribute.convert_to_datatype(value),
                         datatype=attribute.datatype))
            )

    def _attribute_value_generator(self,
                                   attribute: OntologyAttribute) \
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
        for literal in self.session.graph.objects(self.iri, attribute.iri):
            # TODO: Recreating the literal to get a vector from
            #  literal.toPython() should not be necessary, find out why it
            #  is happening.
            literal = Literal(str(literal), datatype=literal.datatype,
                              lang=literal.language)
            yield literal.toPython()

    def _attribute_generator(self) \
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

        for predicate in self.session.graph.predicates(self.iri, None):
            obj = self.session.from_identifier(predicate)
            if isinstance(obj, OntologyAttribute):
                yield obj

    def _attribute_and_value_generator(self) \
            -> Iterator[Tuple[OntologyAttribute,
                              Iterator[RDFCompatibleType]]]:
        """Returns a generator of the both attributes and their values.

        Returns:
            Generator that yields tuples, where the first item is the ontology
            attribute and the second a generator of values for such attribute.
        """
        for attribute in self._attribute_generator():
            yield attribute, \
                self._attribute_value_generator(attribute)

    class _AttributeSet(_ObjectSet):
        """A set interface to an ontology individual's attributes.

        This class looks like and acts like the standard `set`, but it
        is an interface to the `_add_attributes`, _set_attributes`,
        `_delete_attributes` and `_attribute_value_generator` methods.

        When an instance is read, the method `_attribute_value_generator` is
        used to fetch the data. When it is modified in-place, the methods
        `_add_attributes`, `_set_attributes`, and `_delete_attributes` are used
        to reflect the changes.

        This class does not hold any attribute-related information itself, thus
        it is safe to spawn multiple instances linked to the same attribute
        and ontology individual (when single-threading).
        """
        _predicate: OntologyAttribute
        _individual: "OntologyIndividual"

        @property
        def _underlying_set(self) -> Set[RDFCompatibleType]:
            """The set of values assigned to the attribute `self._predicate`.

            Returns:
                The mentioned underlying set.
            """
            return set(
                self._individual._attribute_value_generator(
                    attribute=self._predicate))

        def __init__(self,
                     attribute: OntologyAttribute,
                     individual: "OntologyIndividual"):
            """Fix the liked OntologyAttribute and ontology individual."""
            super().__init__(attribute, individual)

        def __len__(self) -> int:
            """Return len(self)."""
            i = 0
            for x in self._individual._attribute_value_generator(
                    attribute=self._predicate):
                i += 1
            return i

        def __and__(self, other: set) -> Set[RDFCompatibleType]:
            """Return self&other."""
            return super().__and__(other)

        def __ior__(self, other: Set[RDFCompatibleType]):
            """Return self|=other."""
            self._individual._add_attributes(self._predicate, other)
            return self

        def __iand__(self, other: Set[RDFCompatibleType]):
            """Return self&=other."""
            underlying_set = self._underlying_set
            intersection = underlying_set.intersection(other)
            removed = underlying_set.difference(intersection)
            self._individual._delete_attributes(self._predicate, removed)
            return self

        def __ixor__(self, other: Set[RDFCompatibleType]):
            """Return self^=other."""
            self._individual._set_attributes(self._predicate,
                                             self._underlying_set ^ other)
            return self

        def __isub__(self, other: Any):
            """Return self-=other."""
            if isinstance(other, (Set, MutableSet)):
                # Apparently instances of MutableSet are not instances of Set.
                self._individual._delete_attributes(self._predicate,
                                                    self._underlying_set
                                                    & set(other))
            else:
                self._individual._delete_attributes(
                    self._predicate, self._underlying_set & {other})
            return self

        def clear(self):
            """Remove all elements from this set.

            This also removed all the values assigned to the attribute
            linked to this set for the cuds linked to this set.
            """
            self._individual._set_attributes(self._predicate, set())

        def pop(self) -> RDFCompatibleType:
            """Remove and return an arbitrary set element.

            Raises KeyError if the set is empty.
            """
            result = self._underlying_set.pop()
            self._individual._delete_attributes(self._predicate, {result})
            return result

        def difference(self, other: Iterable) -> Set[RDFCompatibleType]:
            """Return the difference of two or more sets as a new set.

            (i.e. all elements that are in this set but not the others.)
            """
            return super().difference(other)

        def difference_update(self, other: Iterable):
            """Remove all elements of another set from this set."""
            self._individual._delete_attributes(
                self._predicate, self._underlying_set.intersection(other))

        def discard(self, other: Any):
            """Remove an element from a set if it is a member.

            If the element is not a member, do nothing.
            """
            self._individual._delete_attributes(self._predicate, {other})

        def intersection(self, other: set) -> Set[RDFCompatibleType]:
            """Return the intersection of two sets as a new set.

            (i.e. all elements that are in both sets.)
            """
            return super().intersection(other)

        def add(self, other: RDFCompatibleType):
            """Add an element to a set.

            This has no effect if the element is already present.
            """
            return super().add(other)

        def remove(self, other: Any):
            """Remove an element from a set; it must be a member.

            If the element is not a member, raise a KeyError.
            """
            if other in self._underlying_set:
                self._individual._delete_attributes(self._predicate, {other})
            else:
                raise KeyError(f"{other}")

        def update(self, other: Iterable):
            """Update a set with the union of itself and others."""
            self._individual._add_attributes(
                self._predicate, set(other).difference(self._underlying_set))

    # ↑ -------------- ↑
    # Attribute handling

    def __init__(self,
                 uid: Optional[UID] = None,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False,
                 class_: Optional['OntologyClass'] = None,
                 attributes: Optional[
                     Dict['OntologyAttribute',
                          Iterable[RDFCompatibleType]]] = None,
                 ) -> None:
        """Initialize the ontology individual."""
        if uid is None:
            uid = UID()
        elif not isinstance(uid, UID):
            raise Exception(f"Tried to initialize an ontology individual with "
                            f"uid {uid}, which is not a UID object.")
        self._ontology_classes = []
        triples = set(triples) if triples is not None else set()
        # Attribute triples.
        attributes = attributes or dict()
        triples |= set((uid.to_iri(), k.iri, Literal(k.convert_to_datatype(e),
                                                     datatype=k.datatype))
                       for k, v in attributes.items() for e in v)
        # Class triples.
        if class_:
            triples |= {(uid.to_iri(), RDF.type, class_.iri)}
            self._ontology_classes += [class_]
        # extra_class = False
        # Extra triples
        for s, p, o in triples:
            # if p == RDF.type:
            #     extra_class = True
            triples.add((s, p, o))
            # TODO: grab extra class from tbox, add it to _ontology_classes.

        # Determine whether class was assigned (currently unused).
        # class_assigned = bool(class_) or extra_class
        # if not class_assigned:
            # raise TypeError(f"No ontology class associated with {self}! "
            #                 f"Did you install the required ontology?")
            # logger.warning(f"No ontology class associated with {self}! "
            #               f"Did you install the required ontology?")
            # pass

        # When the construction is complete, the session is switched.
        super().__init__(uid, session, triples or None, merge=merge)
        logger.debug("Instantiated ontology individual %s" % self)
