"""An ontology individual."""

import functools
import itertools
import logging
from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import (Any, Dict, Iterable, Iterator, List, MutableSet,
                    Optional, Set, TYPE_CHECKING, Tuple, Type, Union)

from rdflib import RDF, Literal, URIRef
from rdflib.term import Identifier, Node

from simphony_osp.core.ontology.annotation import OntologyAnnotation
from simphony_osp.core.ontology.attribute import OntologyAttribute
from simphony_osp.core.ontology.entity import OntologyEntity
from simphony_osp.core.ontology.oclass import OntologyClass
from simphony_osp.core.ontology.relationship import OntologyRelationship
from simphony_osp.core.ontology.utils import DataStructureSet
from simphony_osp.core.utils.datatypes import (
    AttributeValue, AnnotationValue, ATTRIBUTE_VALUE_TYPES, OntologyPredicate,
    RelationshipValue, PredicateValue, Triple, UID)
from simphony_osp.core.utils.cuba_namespace import cuba_namespace

if TYPE_CHECKING:
    from simphony_osp.core.session import Session

logger = logging.getLogger(__name__)


class ResultEmptyError(Exception):
    """The result is unexpectedly empty."""


class MultipleResultsError(Exception):
    """Only a single result is expected, but there were multiple."""


class ObjectSet(DataStructureSet, ABC):
    """A set interface to an ontology individual's neighbors.

    This class looks like and acts like the standard `set`, but it
    is a template to implement classes that use either the attribute
    interface or the methods `relationships_connect`,
    `relationships_disconnect` and `relationships_iter` from
    the ontology individual.

    When an instance is read or when it is modified in-place,
    the interfaced methods are used to reflect the changes.

    This class does not hold any object-related information itself, thus
    it is safe to spawn multiple instances linked to the same property
    and ontology individual (when single-threading).
    """

    _predicate: Optional[OntologyPredicate]
    """Main predicate to which this object refers. It will be used
    whenever there is ambiguity on which predicate to use. Can be set to
    None, usually meaning all predicates (see the specific
    implementations of this class: `AttributeSet`,
    `RelationshipSet` and `AnnotationSet`)."""

    _individual: "OntologyIndividual"
    """The ontology individual to which this object is linked to.
    Whenever the set is modified, the modification will affect this ontology
    individual."""

    @property
    def individual(self) -> "OntologyIndividual":
        """Ontology individual that this set refers to."""
        return self._individual

    @property
    def predicate(self) -> Union[OntologyPredicate]:
        """Predicate that this set refers to."""
        return self._predicate

    @property
    def _predicates(self) -> Optional[Union[
        Set[OntologyAttribute],
        Set[OntologyRelationship],
        Set[OntologyAnnotation],
    ]]:
        """All the predicates to which this instance refers to.

        Returns:
            Such predicates, or `None` if no main predicate is
            associated with this `ObjectSet`.
        """
        return self._predicate.subclasses \
            if self._predicate is not None else \
            None

    def __init__(self,
                 predicate: Optional[OntologyPredicate],
                 individual: "OntologyIndividual"):
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
            + f'of ontology individual {self._individual}>'

    def one(self) -> Union[
        AnnotationValue,
        AttributeValue,
        RelationshipValue,
    ]:
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

    def any(self) -> Optional[Union[
        AnnotationValue,
        AttributeValue,
        RelationshipValue,
    ]]:
        """Return any element of the set.

        Returns:
            Any element from the set if the set is not empty, else None.
        """
        return next(iter(self), None)

    def all(self) -> "ObjectSet":
        """Return all elements from the set.

        Returns:
            All elements from the set, namely the set itself.
        """
        return self


class AttributeSet(ObjectSet):
    """A set interface to an ontology individual's attributes.

    This class looks like and acts like the standard `set`, but it
    is an interface to the `attributes_add`, attributes_set`,
    `attributes_delete`, `attributes_value_contains` and
    `attributes_value_generator` methods.

    When an instance is read, the methods `attributes_value_generator`
    and `attributes_value_contains` are used to fetch the data. When it
    is modified in-place, the methods `attributes_add`, `attributes_set`,
    and `attributes_delete` are used to reflect the changes.

    This class does not hold any attribute-related information itself, thus
    it is safe to spawn multiple instances linked to the same attribute
    and ontology individual (when single-threading).
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
                self._individual.attributes_generator())
            # The code below is technically true, but makes no
            #  difference due to how `attributes_generator` is written.
            # predicates = set(itertools.chain(
            #    subclasses
            #    for attributes in
            #    self._individual.attributes_generator(_notify_read=True)
            #    for subclasses in attributes.subclasses
            # ))
        return predicates

    def __init__(self,
                 attribute: Optional[OntologyAttribute],
                 individual: "OntologyIndividual"):
        """Fix the liked OntologyAttribute and ontology individual."""
        super().__init__(attribute, individual)

    def __iter__(self) -> Iterator[AttributeValue]:
        """The values assigned to the referred predicates.

        Such predicates are the main attribute and its subclasses.

        Returns:
            The mentioned values.
        """
        yielded: Set[AttributeValue] = set()
        for value in itertools.chain(*(
                self._individual.attributes_value_generator(
                    attribute=attribute)
                for attribute in self._predicates
        )):
            if value not in yielded:
                yielded.add(value)
                yield value

    def __contains__(self, item: AttributeValue) -> bool:
        """Check whether a value is assigned to the attribute."""
        return any(
            self._individual.attributes_value_contains(attribute, item)
            for attribute in self._predicates
        )

    def update(self, other: Iterable[AttributeValue]) -> None:
        """Update the set with the union of itself and others."""
        underlying_set = set(self)
        added = set(other).difference(underlying_set)
        self._individual.attributes_add(self._predicate, added)

    def intersection_update(self, other: Iterable[AttributeValue]) -> \
            None:
        """Update the set with the intersection of itself and another."""
        underlying_set = set(self)
        intersection = underlying_set.intersection(other)
        removed = underlying_set.difference(intersection)
        for attribute in self._predicates:
            self._individual.attributes_delete(attribute, removed)

    def difference_update(self, other: Iterable[AttributeValue]) -> \
            None:
        """Remove all elements of another set from this set."""
        removed = set(self) & set(other)
        for attribute in self._predicates:
            self._individual.attributes_delete(attribute, removed)

    def symmetric_difference_update(self, other: Set[AttributeValue]) \
            -> None:
        """Update set with the symmetric difference of it and another."""
        underlying_set = set(self)
        symmetric_difference = underlying_set.symmetric_difference(other)
        added = symmetric_difference.difference(underlying_set)
        self._individual.attributes_add(self._predicate, added)
        removed = underlying_set.difference(symmetric_difference)
        for attribute in self._predicates:
            self._individual.attributes_delete(attribute,
                                               removed)


class RelationshipSet(ObjectSet):
    """A set interface to an ontology individual's relationships.

    This class looks like and acts like the standard `set`, but it
    is an interface to the `relationships_connect`, `relationships_disconnect`
    and `relationships_iter` methods.

    When an instance is read, the method `relationships_iter` is used to fetch
    the data. When it is modified in-place, the methods
    `relationships_connect` and `relationships_disconnect` are used to
    reflect the changes.

    This class does not hold any relationship-related information itself,
    thus it is safe to spawn multiple instances linked to the same
    relationship and ontology individual (when single-threading).
    """
    _predicate: Optional[OntologyRelationship]
    _class_filter: Optional[OntologyClass]
    _uid_filter: Optional[Tuple[UID]]
    _inverse: bool = False

    def __init__(self,
                 relationship: Optional[OntologyRelationship],
                 individual: 'OntologyIndividual',
                 oclass: Optional[OntologyClass] = None,
                 inverse: bool = False,
                 uids: Optional[Iterable[UID]] = None):
        """Fix the liked OntologyRelationship and ontology individual."""
        if relationship is not None \
                and not isinstance(relationship, OntologyRelationship):
            raise TypeError("Found object of type %s. "
                            "Should be an OntologyRelationship."
                            % type(relationship))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError("Found object of type %s. Should be "
                            "an OntologyClass."
                            % type(oclass))
        uids = tuple(uids) if uids is not None else None
        if uids is not None:
            for uid in uids:
                if not isinstance(uid, UID):
                    raise TypeError(
                        "Found object of type %s. Should be an UID."
                        % type(uid))

        self._class_filter = oclass
        self._inverse = inverse
        self._uid_filter = uids
        super().__init__(relationship, individual)

    def __iter__(self) -> Iterator['OntologyIndividual']:
        """Iterate over individuals assigned to `self._predicates`.

        Note: no class filter.

        Returns:
            The mentioned underlying set.
        """
        if self._uid_filter:
            last_identifier = None
            for i, r, t in self.iter_low_level():
                if i == last_identifier:
                    continue
                elif (r, t) == (None, None):
                    yield None
                else:
                    item = self._individual.session.from_identifier(i)
                    if not self._class_filter or item.is_a(self._class_filter):
                        yield item
                    else:
                        yield None
                last_identifier = i
        else:
            yielded: Set[Node] = set()
            for i, r, t in self.iter_low_level():
                item = self._individual.session.from_identifier(i)
                if i in yielded or (
                        self._class_filter
                        and not item.is_a(self._class_filter)
                ):
                    continue
                yielded.add(i)
                yield item

    def __contains__(self, item: "OntologyIndividual") -> bool:
        """Check if an individual is connected via the relationship."""
        if item not in self.individual.session:
            return False

        original_uid_filter = self._uid_filter
        try:
            self._uid_filter = (item.uid, )
            return next(iter(self)) is not None
        finally:
            self._uid_filter = original_uid_filter

    def __invert__(self) -> 'RelationshipSet':
        """Get the inverse RelationshipSet."""
        return self.inverse

    @property
    def inverse(self) -> 'RelationshipSet':
        """Get the inverse RelationshipSet.

        Returns a RelationshipSet that works in the inverse direction: the
        ontology individuals displayed are the ones which are the subject of
        the relationship.
        """
        return RelationshipSet(relationship=self._predicate,
                               individual=self.individual,
                               oclass=self._class_filter,
                               inverse=not self._inverse)

    @staticmethod
    def prevent_class_filtering(func):
        """Decorator breaking methods when class filtering is enabled."""
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
    def update(self, other: Iterable['OntologyIndividual']) -> None:
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
            self._individual.relationships_connect(individual,
                                                   rel=self._predicate)

    @prevent_class_filtering
    def intersection_update(self, other: Iterable['OntologyIndividual']) \
            -> None:
        """Update the set with the intersection of itself and another."""
        # Note: please read the comment on the `update` method.
        underlying_set = set(self)
        result = underlying_set.intersection(other)

        removed = underlying_set.difference(result)
        if removed:
            for rel in self._predicates:
                self._individual.relationships_disconnect(*removed, rel=rel)

        added = result.difference(underlying_set)
        self._individual.relationships_connect(*added, rel=self._predicate)

    @prevent_class_filtering
    def difference_update(self, other: Iterable['OntologyIndividual']) \
            -> None:
        """Remove all elements of another set from this set."""
        # Note: please read the comment on the `update` method.
        removed = set(self) & set(other)
        if removed:
            for rel in self._predicates:
                self._individual.relationships_disconnect(*removed, rel=rel)

    @prevent_class_filtering
    def symmetric_difference_update(self,
                                    other: Iterable['OntologyIndividual']) \
            -> None:
        """Update with the symmetric difference of it and another."""
        # Note: please read the comment on the `update` method.
        underlying_set = set(self)
        result = underlying_set.symmetric_difference(other)

        removed = underlying_set.difference(result)
        if removed:
            for rel in self._predicates:
                self._individual.relationships_disconnect(*removed, rel=rel)

        added = result.difference(underlying_set)
        self._individual.relationships_connect(*added, rel=self._predicate)

    def iter_low_level(self) -> Iterator[
            Tuple[
                Node,
                Optional[Node],
                Optional[bool]
            ]]:
        """Iterate over individuals assigned to `self._predicates`.

        Note: no class filter.

        Returns:
            The mentioned underlying set.
        """
        # Get the predicate IRIs (p) to be considered.
        # Let x be `self._individual`.
        #  - direct_allowed: Triples of the form (x, p, o) will result in o
        #    being a candidate to be yielded.
        #  - inverse_allowed: Triples of the form (s, p, x) will result in s
        #    being a candidate to be yielded.
        direct_allowed = set(p.identifier for p in self._predicates)
        inverse_allowed = set(rel.identifier
                              for rel in filter(None,
                                                (p.inverse
                                                 for p in self._predicates))
                              )
        if self._inverse:
            direct_allowed, inverse_allowed = inverse_allowed, direct_allowed

        # Get the individuals connected to `self._individual` through the
        # allowed predicates, that is, o and s from the last comment.
        individual = self._individual.identifier
        graph = self._individual.session.graph
        if self._uid_filter is None:
            predicate_individual_direct = (
                (o, p)
                for p, o in graph.predicate_objects(individual)
                if p in direct_allowed
            )
            predicate_individual_inverse = (
                (s, p)
                for s, p in graph.subject_predicates(individual)
                if p in inverse_allowed
            )
            individuals_and_relationships = chain(
                ((o, p, True)
                 for o, p in predicate_individual_direct),
                ((s, p, False)
                 for s, p in predicate_individual_inverse)
            )
        else:
            # In this case, we respect the ordering of the `_uid_filter` and
            # yield `(uid.to_identifier(), None, None)` when there is not an
            # allowed connection between `self._individual` the individual
            # represented by `uid`.
            def individuals_and_relationships():
                for uid in self._uid_filter:
                    identifier = uid.to_identifier()
                    found = chain(
                        ((p, True)
                         for p in graph.predicates(individual, identifier)
                         if p in direct_allowed),
                        ((p, False)
                         for p in graph.predicates(identifier, individual)
                         if p in inverse_allowed),
                    )
                    first = next(found, (None, None))
                    yield identifier, *first
                    if first != (None, None):
                        yield from ((identifier, *f) for f in found)

            individuals_and_relationships = individuals_and_relationships()

        yield from individuals_and_relationships


class AnnotationSet(ObjectSet):
    """A set interface to an ontology individual's annotations.

    This class looks like and acts like the standard `set`, but it is an
    interface to the methods from `OntologyIndividual` that manage the
    annotations.

    This class does not hold any annotation-related information itself,
    thus it is safe to spawn multiple instances linked to the same
    relationship and ontology individual (when single-threading).
    """

    _predicate: OntologyAnnotation

    def __init__(self,
                 annotation: Optional[OntologyAnnotation],
                 individual: "OntologyIndividual") -> None:
        """Fix the linked OntologyAnnotation and ontology individual."""
        super().__init__(annotation, individual)

    def __iter__(self) -> Iterator[AnnotationValue]:
        """Iterate over annotations linked to the individual."""
        yield from self._individual.annotations_value_generator(
            annotation=self._predicate)

    def __contains__(self, item) -> bool:
        """Determine whether the individual is annotated with an item."""
        return super().__contains__(item)

    def update(self, other: Iterable[AnnotationValue]) -> None:
        """Update the set with the union of itself and other."""
        self._individual.annotations_add(annotation=self._predicate,
                                         values=other)

    def intersection_update(
            self,
            other: Iterable[AnnotationValue]) -> None:
        """Update the set with the intersection of itself and another."""
        self._individual.annotations_set(annotation=self._predicate,
                                         values=other)

    def difference_update(self,
                          other: Iterable[Any]) -> None:
        """Return self-=other."""
        self._individual.annotations_delete(annotation=self._predicate,
                                            values=set(self) & set(other))

    def symmetric_difference_update(
            self,
            other: Iterable[AnnotationValue]) -> None:
        """Return self^=other."""
        self._individual.annotations_set(self._predicate,
                                         set(self)
                                         ^ set(other))


class OntologyIndividual(OntologyEntity):
    """An ontology individual."""

    rdf_identifier = Identifier

    def __init__(self,
                 uid: Optional[UID] = None,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False,
                 class_: Optional[OntologyClass] = None,
                 attributes: Optional[
                     Dict['OntologyAttribute',
                          Iterable[AttributeValue]]] = None,
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
        # for s, p, o in triples:
            # if p == RDF.type:
            #     extra_class = True
            # triples.add((s, p, o))
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

    # Public API
    # ↓ ------ ↓

    @property
    def oclass(self) -> Optional[OntologyClass]:
        """Get the ontology class of the ontology individual.

        Returns:
            The ontology class of the ontology individual. If the individual
            belongs to multiple classes, then ONLY ONE of them is returned.
            When the ontology individual does not belong to any ontology class.
        """
        oclasses = self.oclasses
        return oclasses[0] if oclasses else None

    @oclass.setter
    def oclass(self, value: OntologyClass) -> None:
        """Set the ontology class of the ontology individual.

        Args:
            value: The new ontology class of the ontology individual.
        """
        self.oclasses = {value}

    @property
    def oclasses(self) -> Tuple[OntologyClass]:
        """Get the ontology classes of this ontology individual.

        Returns:
            A tuple with all the ontology classes of the ontology
            individual. When the individual has no classes, the tuple is empty.
        """
        return tuple(self.session.ontology.from_identifier(o)
                     for o in self.session.graph.objects(self.identifier,
                                                         RDF.type))

    @oclasses.setter
    def oclasses(self, value: Iterable[OntologyClass]) -> None:
        """Set the ontology classes of this ontology individual.

        Args:
            value: New ontology classes of the ontology individual.
        """
        identifiers = set()
        for x in value:
            if not isinstance(x, OntologyClass):
                raise TypeError(f"Expected {OntologyClass}, not {type(x)}.")
            identifiers.add(x.identifier)
        self.session.graph.remove((self.identifier, RDF.type, None))
        for x in identifiers:
            self.session.graph.add((self.identifier, RDF.type, x))

    def is_a(self, oclass: OntologyClass) -> bool:
        """Check if the individual is an instance of the given ontology class.

        Args:
            oclass: The ontology class to test against.

        Returns:
            Whether the ontology individual is an instance of such ontology
                class.
        """
        return any(oc in oclass.subclasses for oc in self.oclasses)

    def __dir__(self) -> Iterable[str]:
        """Show the individual's attributes as autocompletion suggestions."""
        result = iter(())
        attributes_and_namespaces = (
            (attr, ns)
            for oclass in self.oclasses
            for attr in oclass.attribute_declaration
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

    def __getattr__(self, name: str) -> AttributeValue:
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
        attr = self._attributes_get_by_name(name)
        values = self.attributes_value_generator(attr)
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
                    value: Optional[
                        Union[AttributeValue,
                              Set[AttributeValue]]
                    ]) -> None:
        """Set the value(s) of an attribute.

        Args:
            name: The name of the attribute.
            value: The new value.

        Raises:
            AttributeError: Unknown attribute name.
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        try:
            attr = self._attributes_get_by_name(name)
            value = {value} if value is not None else set()
            self.attributes_set(attr, value)
        except AttributeError as e:
            # Might still be an attribute of a subclass of OntologyIndividual.
            if hasattr(self, name):
                super().__setattr__(name, value)
            else:
                raise e

    def __getitem__(
            self,
            rel: OntologyPredicate) -> Union[AttributeSet,
                                             RelationshipSet,
                                             AnnotationSet]:
        """Retrieve linked individuals, attribute values or annotation values.

        The subscripting syntax `individual[rel]` allows:
        - When `rel` is an OntologyAttribute, to obtain a set containing all
          the values assigned to the specified attribute. Such set can be
          modified in-place to change the assigned values.
        - When `rel` is an OntologyRelationship, to obtain a set containing
          all ontology individuals objects that are connected to `individual`
          through rel. Such set can be modified in-place to modify the
          existing connections.
        - When `rel` is an OntologyAnnotation, to obtain a set containing
          all the annotation values assigned to the specified annotation
          property. Such set can be modified in-place to modify the existing
          connections.

        The reason why a set is returned and not a list, or any other
        container allowing repeated elements, is that the underlying RDF
        graph does not accept duplicate statements.

        Args:
            rel: An ontology attribute, an ontology relationship or an ontology
                annotation (OWL datatype property, OWL object property,
                OWL annotation property).

        Raises:
            TypeError: Trying to use something that is neither an
                OntologyAttribute, an OntologyRelationship or an
                OntologyAnnotation as index.
        """
        if isinstance(rel, OntologyAttribute):
            set_class = AttributeSet
        elif isinstance(rel, OntologyRelationship):
            set_class = RelationshipSet
        elif isinstance(rel, OntologyAnnotation):
            set_class = AnnotationSet
        else:
            raise TypeError(f'Ontology individual indices must be ontology '
                            f'relationships, ontology attributes, '
                            f'or ontology annotations, not {type(rel)}.')
        return set_class(rel, self)

    def __setitem__(
            self,
            rel: OntologyPredicate,
            values: Optional[Union[PredicateValue,
                                   Set[PredicateValue]]]
    ) -> None:
        """Manages object, data and annotation properties.

        The subscripting syntax `individual[rel] = ` allows,

        - When `rel` is an OntologyRelationship, to replace the list of
          ontology individuals that are connected to `individual` through rel.
        - When `rel` is an OntologyAttribute, to replace the values of
          such attribute.
        - When `rel` is an OntologyAnnotation, to replace the annotation
          values of such annotation property.

        This function only accepts hashable objects as input, as the
        underlying RDF graph does not accept duplicate statements.

        Args:
            rel: Either an ontology attribute, an ontology relationship or
                an ontology annotation (OWL datatype property, OWL object
                property, OWL annotation property).
            values: Either a single element compatible with the OWL standard
                (this includes ontology individuals) or a set of such
                elements.

        Raises:
            TypeError: Trying to assign attributes using an object property,
                trying to assign ontology individuals using a data property,
                trying to use something that is neither an OntologyAttribute,
                an OntologyRelationship nor an OntologyAnnotation as index.
        """
        if isinstance(values, ObjectSet) \
                and values.individual is self and values.predicate is rel:
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

        # Classify the values by type.
        values = self._classify_by_type(values)

        # Perform assignments.
        if isinstance(rel, OntologyRelationship):
            if ((len(values) > 0 and OntologyIndividual not in values)
                    or len(values) > 1):
                raise TypeError(f'Trying to assign python objects which are '
                                f'not ontology individuals using an object '
                                f'property {rel}.')
            assigned = set(
                values.get(OntologyIndividual, set())
            )
            current = RelationshipSet(rel, self, oclass=None)

            add = assigned - current
            remove = current - assigned

            current -= remove
            current |= add
        elif isinstance(rel, OntologyAttribute):
            if ((len(values) > 0
                 and all(x not in values
                         for x in (ATTRIBUTE_VALUE_TYPES, Literal)))
                    or len(values) > 2):
                raise TypeError(f'Trying to assign python objects which '
                                f'cannot be interpreted as literals '
                                f'using a data property {rel}.')
            assigned = set(
                values.get(ATTRIBUTE_VALUE_TYPES, set())
            ) | set(
                values.get(Literal, set())
            )
            current = AttributeSet(rel, self)

            add = assigned - current
            remove = current - assigned

            current |= add
            current -= remove
        elif isinstance(rel, OntologyAnnotation):
            # TODO: Use a unit of work pattern here like above to only
            #  remove and add, rather than replacing.
            self.annotations_set(rel, values)
        else:
            raise TypeError(f'Ontology individual indices must be ontology '
                            f'relationships, ontology attributes or ontology '
                            f'annotations not {type(rel)}.')

    def __delitem__(self, rel: OntologyPredicate):
        """Delete all objects attached through rel.

        Args:
            rel: Either an ontology attribute, an ontology relationship or
                an ontology annotation (OWL datatype property, OWL object
                property, OWL annotation property).
        """
        self.__setitem__(rel=rel, values=set())

    def add(self,
            *individuals: "OntologyIndividual",
            rel: Optional[Union[OntologyRelationship, Identifier]] = None
            ) -> Union["OntologyIndividual", List["OntologyIndividual"]]:
        """Link CUDS objects to another CUDS objects.

        If the added objects are associated with the same session,
        only a link is created. Otherwise, a deepcopy is made and added
        to the session of this CUDS object.

        Args:
            individuals: The objects to be added
            rel: The relationship between the objects.

        Raises:
            TypeError: Either
                - no relationship given and no default specified, or
                - objects not of type CUDS provided as positional arguments.
            ValueError: Added a CUDS object that is already in the container.
            Note: in fact, the exception raised is
            `ExistingIndividualException`, but it is a subclass of
            `ValueError`.

        Returns:
            The CUDS objects that have been added, associated with the
                session of the current CUDS object. The result type is a list
                if more than one CUDS object was provided.
        """
        for x in individuals:
            if not isinstance(x, OntologyIndividual):
                raise TypeError(f'Expected {OntologyIndividual} objects, not '
                                f'{type(x)}.')

        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier(rel)
        rel = rel or next((oclass.namespace.default_relationship
                           for oclass in self.oclasses), None)
        if rel is None:
            raise TypeError("Missing argument 'rel'! No default "
                            "relationship specified for namespace %s."
                            % self.oclass.namespace)

        self.relationships_connect(*individuals, rel=rel)
        result = (self.session.from_identifier(i.identifier)
                  for i in individuals)
        return next(result) if len(individuals) == 1 else list(result)

    class ExistingIndividualException(ValueError):
        """To be raised when a provided CUDS is already linked."""
        pass

    def get(self,
            *uids: UID,
            rel: Optional[Union[
                OntologyRelationship,
                Identifier]] = cuba_namespace.activeRelationship,
            oclass: OntologyClass = None,
            return_rel: bool = False) -> Union[
        "RelationshipSet",
        Optional["OntologyIndividual"],
        Tuple[Optional["OntologyIndividual"], ...],
        Tuple[Tuple["OntologyIndividual", OntologyRelationship]]
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
            Calls without `*uids` (RelationshipSet): The result of the
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
        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier(rel)

        if uids and oclass is not None:
            raise ValueError("Do not specify both uids and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise TypeError("Found object of type %s passed to argument rel. "
                            "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError("Found object of type %s passed to argument "
                            "class. Should be an OntologyClass."
                            % type(oclass))

        relationship_set = RelationshipSet(rel, self, oclass=oclass,
                                           uids=uids or None)

        if not return_rel:
            if not uids:
                return relationship_set
            else:
                return next(iter(relationship_set)) \
                    if len(uids) == 1 else tuple(
                    relationship_set)
        else:
            result = []
            for (i, r, t) in relationship_set.iter_low_level():
                if not t:
                    continue
                session = self.session
                result += [
                    (session.from_identifier(i),
                     session.ontology.from_identifier(r))
                ]
            if len(uids) == 1:
                return result[0] if result else None
            else:
                return tuple(result)

    def iter(self,
             *uids: UID,
             rel: Optional[Union[
                 OntologyRelationship,
                 Identifier]] = cuba_namespace.activeRelationship,
             oclass: Optional[OntologyClass] = None,
             return_rel: bool = False) -> Union[
        Iterator["OntologyIndividual"],
        Iterator[Optional["OntologyIndividual"]],
        Iterator[Tuple["OntologyIndividual", OntologyRelationship]],
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
        """
        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier(rel)

        if uids and oclass is not None:
            raise ValueError("Do not specify both uids and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise TypeError("Found object of type %s passed to argument rel. "
                            "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError("Found object of type %s passed to argument "
                            "class. Should be an OntologyClass."
                            % type(oclass))

        relationship_set = RelationshipSet(rel, self, oclass=oclass,
                                           uids=uids or None)

        if not return_rel:
            yield from iter(relationship_set)
        else:
            for (i, r, t) in relationship_set.iter_low_level():
                if not t:
                    continue
                session = self.session
                yield (
                    (session.from_identifier(i),
                     session.ontology.from_identifier(r))
                )

    def update(self, *individuals: "OntologyIndividual") \
            -> Union["OntologyIndividual", List["OntologyIndividual"]]:
        """Update the Cuds object.

        Updates the object by providing updated versions of CUDS objects
        that are directly in the container of this CUDS object.
        The updated versions must be associated with a different session.

        Args:
            individuals: The updated versions to use to update the current
                object.

        Raises:
            ValueError: Provided a CUDS objects is not in the container of the
                current CUDS
            ValueError: Provided CUDS object is associated with the same
                session as the current CUDS object. Therefore, it is not an
                updated version.
            TypeError: Provided objects that are not of type
                OntologyIndividual as positional arguments.

        Returns:
            The CUDS objects that have been updated, associated with the
            session of the current CUDS object. Result type is a list,
            if more than one CUDS object is returned.
        """
        for x in individuals:
            if not isinstance(x, OntologyIndividual):
                raise TypeError(f'Expected {OntologyIndividual} objects, not '
                                f'{type(x)}.')

        result = set()
        for x in individuals:
            try:
                pointer = self.session.from_identifier(x.identifier)
                result.add(pointer)
            except KeyError:
                raise ValueError(f'Cannot update because individual {x} not '
                                 f'added.')
            if x in self.session:
                raise ValueError("Please provide CUDS objects from a "
                                 "different session to update()")

        for x in individuals:
            self.session.update(x)

        return result.pop() if len(individuals) == 1 else result

    def remove(self,
               *uids_or_individuals: Union["OntologyIndividual", UID],
               rel: Optional[Union[
                   OntologyRelationship,
                   Identifier]] = cuba_namespace.activeRelationship,
               oclass: Optional[OntologyClass] = None) -> None:
        """Remove elements from the CUDS object.

        Expected calls are remove(), remove(*uids_or_individuals),
        remove(rel=___), remove(oclass=___),
        remove(*uids_or_individuals, rel=___), remove(rel=___, oclass=___).

        Args:
            uids_or_individuals: Optionally, specify the UIDs of the elements
                to remove or provide the elements themselves.
            rel: Only remove individuals which are connected by subclass of the
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
        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier(rel)

        if uids_or_individuals and oclass is not None:
            raise ValueError("Do not specify both uids and oclass.")
        if rel is not None and not isinstance(rel, OntologyRelationship):
            raise TypeError("Found object of type %s passed to argument rel. "
                            "Should be an OntologyRelationship." % type(rel))
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError("Found object of type %s passed to argument "
                            "oclass. Should be an OntologyClass."
                            % type(oclass))
        uids = list()
        for x in uids_or_individuals:
            if isinstance(x, OntologyIndividual):
                uids += [x.uid]
            elif isinstance(x, UID):
                uids += [x]
            else:
                raise TypeError(f'Expected {OntologyIndividual} or {UID} '
                                f'objects, not {type(x)}.')

        # Get relationships to be removed.
        consider_relationships = set()
        for predicate in self.session.graph.predicates(self.identifier, None):
            try:
                relationship = self.session.ontology.from_identifier(predicate)
                if isinstance(relationship, OntologyRelationship):
                    consider_relationships |= {relationship}
            except KeyError:
                pass
        if rel:
            consider_relationships &= set(rel.subclasses)

        mapping = OrderedDict((uid, set()) for uid in uids)
        for rel in consider_relationships:
            connected_identifiers = self.session.graph.objects(
                self.identifier, rel.identifier
            )
            connected_uids = map(UID, connected_identifiers)
            if uids:
                connected_uids = set(connected_uids) & set(uids)
            mapping.update(
                (uid, mapping.get(uid, set()) | {rel})
                for uid in connected_uids
            )
        if not mapping:
            logger.warning("Did not remove any Cuds object, because none "
                           "matched your filter.")
            return

        for uid, relationship_set in mapping.items():
            relationship_set = relationship_set or {None}
            for relationship in (r.identifier for r in relationship_set):
                if oclass \
                        and not self.session.from_identifier(
                        uid.to_identifier()).is_a(oclass):
                    continue
                self.session.graph.remove((
                    self.identifier,
                    relationship,
                    uid.to_identifier()
                ))

    # ↑ ------ ↑
    # Public API

    def _get_direct_superclasses(self) -> Iterable['OntologyEntity']:
        return (x for oclass in self.oclasses
                for x in oclass.direct_superclasses)

    def _get_direct_subclasses(self) -> Iterable['OntologyClass']:
        return (x for oclass in self.oclasses
                for x in oclass.direct_subclasses)

    def _get_superclasses(self) -> Iterable['OntologyClass']:
        return (x for oclass in self.oclasses
                for x in oclass.superclasses)

    def _get_subclasses(self) -> Iterable['OntologyClass']:
        return (x for oclass in self.oclasses
                for x in oclass.subclasses)

    # Annotation handling
    # ↓ --------------- ↓

    @staticmethod
    def _classify_by_type(values: Set[PredicateValue]) \
            -> Dict[Type[PredicateValue],
                    PredicateValue]:
        values = {type_: tuple(filter(lambda x: isinstance(x, type_), values))
                  for type_ in (OntologyAnnotation, OntologyAttribute,
                                OntologyClass, OntologyIndividual,
                                OntologyRelationship, ATTRIBUTE_VALUE_TYPES,
                                URIRef, Literal)}
        values = {key: value
                  for key, value in values.items()
                  if value}
        return values

    def annotations_add(self,
                        annotation: OntologyAnnotation,
                        values: Union[Dict[Type[AnnotationValue],
                                           AnnotationValue],
                                      Set[AnnotationValue]]) -> None:
        """Adds annotations to the ontology individual."""
        if not isinstance(values, dict):
            values = self._classify_by_type(values)
        for value in itertools.chain(*(values.get(key, set())
                                       for key in (OntologyAnnotation,
                                                   OntologyAttribute,
                                                   OntologyClass,
                                                   OntologyIndividual,
                                                   OntologyRelationship))
                                     ):
            self.session.graph.add((self.iri, annotation.iri, value.iri))
        for value in values.get(Literal, set()):
            self.session.graph.add(
                (self.iri, annotation.iri,
                 value)
            )
        for value in values.get(ATTRIBUTE_VALUE_TYPES, set()):
            self.session.graph.add(
                (self.iri, annotation.iri,
                 Literal(value))
            )
        for value in values.get(URIRef, set()):
            self.session.graph.add((self.iri, annotation.iri, value))

    def annotations_delete(
            self,
            annotation: OntologyAnnotation,
            values: Union[Dict[Type[AnnotationValue],
                               Union[AnnotationValue]],
                          Set[AnnotationValue]]
    ) -> None:
        """Deletes an annotation from an individual."""
        if not isinstance(values, dict):
            values = self._classify_by_type(values)

        for value in values.get(Literal, set()):
            self.session.graph.remove(
                (self.iri, annotation.iri,
                 value)
            )
        for value in values.get(ATTRIBUTE_VALUE_TYPES, set()):
            self.session.graph.remove(
                (self.iri, annotation.iri,
                 Literal(value))
            )
        for value in values.get(URIRef, set()):
            self.session.graph.remove((self.iri, annotation.iri, value))

    def annotations_set(self,
                        annotation: OntologyAnnotation,
                        values: Union[Dict[Type[AnnotationValue],
                                           AnnotationValue],
                                      Set[AnnotationValue]]) -> None:
        """Replaces the annotations of an individual."""
        if not isinstance(values, dict):
            values = self._classify_by_type(values)

        self.session.graph.remove((self.iri, annotation.iri, None))
        for value in itertools.chain(*(values.get(key, set())
                                       for key in (OntologyAnnotation,
                                                   OntologyAttribute,
                                                   OntologyClass,
                                                   OntologyIndividual,
                                                   OntologyRelationship))
                                     ):
            self.session.graph.add((self.iri, annotation.iri, value.iri))
        for value in values.get(Literal, set()):
            self.session.graph.add(
                (self.iri, annotation.iri,
                 value)
            )
        for value in values.get(ATTRIBUTE_VALUE_TYPES, set()):
            self.session.graph.add(
                (self.iri, annotation.iri,
                 Literal(value))
            )
        for value in values.get(URIRef, set()):
            self.session.graph.add((self.iri, annotation.iri, value))

    def annotations_value_generator(self,
                                    annotation: OntologyAnnotation) \
            -> Iterator[AnnotationValue]:
        """Yields the annotation values applied to the individual."""
        for obj in self.session.graph.objects(self.iri, annotation.iri):
            if isinstance(obj, URIRef):
                try:
                    yield self.session.from_identifier(obj)
                    continue
                except KeyError:
                    pass
                try:
                    yield self.session.ontology.from_identifier(obj)
                    continue
                except KeyError:
                    pass
                yield obj
            elif isinstance(obj, Literal):
                yield obj.toPython()

    # ↑ --------------- ↑
    # Annotation handling

    # Attribute handling
    # ↓ -------------- ↓

    def attributes_get(self) -> Dict[OntologyAttribute,
                                     Set[AttributeValue]]:
        """Get the attributes of this individual as a dictionary."""
        return {attribute: set(value_generator)
                for attribute, value_generator
                in self.attributes_attribute_and_value_generator()}

    def _attributes_get_by_name(self, name: str) -> OntologyAttribute:
        """Get an attribute of this individual by name."""
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

    @staticmethod
    def _attributes_modifier(func):
        """Decorator for functions that perform attribute modifications.

        To be used with `attributes_add`, `attributes_delete` and
        `attributes_set` exclusively. The three functions are extremely
        similar. This decorator covers the code that they share.
        """
        @functools.wraps(func)
        def wrapper(self,
                    attribute: OntologyAttribute,
                    values: Iterable[AttributeValue],
                    *args, **kwargs):
            values = set(values)
            for x in values:
                if not isinstance(x, ATTRIBUTE_VALUE_TYPES):
                    raise TypeError(f"Type '{type(x)}' of object {x} cannot "
                                    f"be set as attribute value, as it is "
                                    f"either incompatible with the OWL "
                                    f"standard or not yet supported by "
                                    f"SimPhoNy.")
            return func(self, attribute, values, *args, **kwargs)
        return wrapper

    # Bind static method to use as decorator.
    _attribute_modifier = _attributes_modifier.__get__(object,
                                                       None)

    @_attribute_modifier
    def attributes_add(self,
                       attribute: OntologyAttribute,
                       values: Iterable[AttributeValue]):
        """Add values to a datatype property.

        If any of the values provided in `values` have already been assigned,
        then they are simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of objects whose types are compatible either
                with the OWL standard's data types for literals or compatible
                with SimPhoNy as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with SimPhoNy as custom data types are given.
        """
        # TODO: prevent the end result having more than one value depending on
        #  ontology cardinality restrictions and/or functional property
        #  criteria.
        for value in filter(lambda v: v is not None, values):
            self.session.graph.add(
                (self.iri, attribute.iri,
                 Literal(attribute.convert_to_datatype(value),
                         datatype=attribute.datatype)))

    @_attribute_modifier
    def attributes_delete(self,
                          attribute: OntologyAttribute,
                          values: Iterable[AttributeValue]):
        """Remove values from a datatype property.

        If any of the values provided in `values` are not present, they are
        simply ignored.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of objects whose types are compatible either
                with the OWL standard's data types for literals or compatible
                with SimPhoNy as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with SimPhoNy as custom data types are given.
        """
        for value in values:
            self.session.graph.remove(
                (self.iri, attribute.iri,
                 Literal(attribute.convert_to_datatype(value),
                         datatype=attribute.datatype)))

    @_attribute_modifier
    def attributes_set(self,
                       attribute: OntologyAttribute,
                       values: Iterable[Union[AttributeValue,
                                              Literal]]):
        """Replace values assigned to a datatype property.

        Args:
            attribute: The ontology attribute to be used for assignments.
            values: An iterable of objects whose types are compatible either
                with the OWL standard's data types for literals or compatible
                with SimPhoNy as custom data types.

        Raises:
            TypeError: When Python objects with types incompatible with the
                OWL standard or with SimPhoNy as custom data types are given.
        """
        # TODO: prevent the end result having more than one value depending on
        #  ontology cardinality restrictions and/or functional property
        #  criteria.
        self.session.graph.remove((self.iri, attribute.iri, None))
        self.attributes_add(attribute, values)

    def attributes_value_generator(self,
                                   attribute: OntologyAttribute) \
            -> Iterator[AttributeValue]:
        """Returns a generator of values assigned to the specified attribute.

        Args:
            attribute: The ontology attribute query for values.

        Returns:
            Generator that returns the attribute values.
        """
        for literal in self.session.graph.objects(self.iri, attribute.iri):
            # TODO: Recreating the literal to get a vector from
            #  literal.toPython() should not be necessary, find out why it
            #  is happening.
            literal = Literal(str(literal), datatype=literal.datatype,
                              lang=literal.language)
            yield literal.toPython()

    def attributes_value_contains(self,
                                  attribute: OntologyAttribute,
                                  value: AttributeValue) \
            -> bool:
        """Whether a specific value is assigned to the specified attribute.

        Args:
            attribute: The ontology attribute query for values.

        Returns:
            Whether the specific value is assigned to the specified
            attribute or not.
        """
        if attribute.datatype in (None, RDF.langString):
            return any(str(value) == str(x)
                       for x in self.session.graph.objects(self.iri,
                                                           attribute.iri)
                       if isinstance(x, Literal))
        else:
            literal = Literal(value, datatype=attribute.datatype)
            literal = Literal(str(literal), datatype=attribute.datatype)
            return literal in self.session.graph.objects(self.iri,
                                                         attribute.iri)

    def attributes_generator(self) \
            -> Iterator[OntologyAttribute]:
        """Returns a generator of the attributes of this CUDS object.

        The generator only returns the OntologyAttribute objects, NOT the
        values.

        Returns:
            Generator that returns the attributes of this CUDS object.
        """
        for predicate in self.session.graph.predicates(self.iri, None):
            try:
                obj = self.session.ontology.from_identifier(predicate)
            except KeyError:
                continue
            if isinstance(obj, OntologyAttribute):
                yield obj

    def attributes_attribute_and_value_generator(self) \
            -> Iterator[Tuple[OntologyAttribute,
                              Iterator[AttributeValue]]]:
        """Returns a generator of both the attributes and their values.

        Returns:
            Generator that yields tuples, where the first item is the ontology
            attribute and the second a generator of values for such attribute.
        """
        for attribute in self.attributes_generator():
            yield attribute, \
                self.attributes_value_generator(attribute)

    # ↑ -------------- ↑
    # Attribute handling

    # Relationship handling
    # ↓ ----------------- ↓

    def relationships_connect(self,
                              *other: "OntologyIndividual",
                              rel: OntologyRelationship):
        """Connect other ontology individuals to this one.

        If the connected object is associated with the same session, only a
        link is created. Otherwise, the information associated with the
        connected object is added to the session of this ontology individual.

        Args:
            other: The ontology individual(s) to connect.
            rel: The relationship to use.

        Raises:
            TypeError: No relationship given.

        Returns:
            The ontology individual that has been connected,
            associated with the session of the current ontology individual
            object.
        """
        for individual in other:
            self.session.merge(individual)
            self.session.graph.add(
                (self.identifier, rel.identifier, individual.identifier))

    def relationships_disconnect(self,
                                 *other: "OntologyIndividual",
                                 rel: Optional[OntologyRelationship] = None):
        """Disconnect ontology individuals from this one.

        Args:
            other: The ontology individual(s) to disconnect. When not
                specified, this ontology individual will be disconnected
                from all connected individuals.
            rel: This ontology individual will be disconnected from `other`
                for relationship `rel`. When not specified, this ontology
                individual will be disconnected from `other` for all
                relationships.
        """
        if rel is None:
            predicates = set()
            for predicate in self.session.graph.predicates(self.identifier,
                                                           None):
                try:
                    relationship = self.session.ontology.from_identifier(
                        predicate)
                    predicates |= {relationship.identifier}
                except KeyError:
                    pass
        else:
            predicates = {rel.identifier}

        other = other if other else {None}
        for item in other:
            s, o = self.identifier, item.identifier \
                if item is not None else None
            for p in predicates:
                self.session.graph.remove((s, p, o))

    def relationships_iter(self,
                           rel: Optional[OntologyRelationship] = None,
                           oclass: Optional[OntologyClass] = None,
                           return_rel: bool = False) \
            -> Iterator["OntologyIndividual"]:
        """Iterate over the connected ontology individuals.

        Args:
            rel: Only return ontology individuals which are connected by
                the given relationship. Defaults to None (any relationship).
            oclass: Only return ontology individuals which belong to the
                given ontology class. Defaults to None (any class).
            return_rel: Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Iterator with the queried ontology individuals.
        """
        entities_and_relationships = (
            (self.session.from_identifier(o), self.session.from_identifier(p))
            for s, p, o in self.session.graph.triples(
                (self.identifier,
                 rel.identifier if rel is not None else None,
                 None))
        )
        if oclass:
            entities_and_relationships = (
                (entity, relationship)
                for entity, relationship in entities_and_relationships
                if oclass == entity)

        if return_rel:
            yield from entities_and_relationships
        else:
            yield from map(lambda x: x[0], entities_and_relationships)

    # ↑ -------------- ↑
    # Relationship handling
