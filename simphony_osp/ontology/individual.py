"""An ontology individual."""
from __future__ import annotations

import functools
import logging
from abc import ABC
from itertools import chain
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    Mapping,
    MutableSet,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

from rdflib import OWL, RDF, Literal, URIRef
from rdflib.term import Identifier, Node

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.operations.operations import OperationsNamespace
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.ontology.utils import DataStructureSet
from simphony_osp.utils.datatypes import (
    ATTRIBUTE_VALUE_TYPES,
    UID,
    AnnotationValue,
    AttributeValue,
    OntologyPredicate,
    PredicateValue,
    RelationshipValue,
    Triple,
)
from simphony_osp.utils.simphony_namespace import simphony_namespace

if TYPE_CHECKING:
    from simphony_osp.ontology.operations.container import ContainerEnvironment
    from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)

RDF_type = RDF.type


class ResultEmptyError(Exception):
    """The result is unexpectedly empty."""


class MultipleResultsError(Exception):
    """Only a single result is expected, but there were multiple."""


class ExistingIndividualException(ValueError):
    """To be raised when a provided CUDS is already linked."""

    pass


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

    _individual: OntologyIndividual
    """The ontology individual to which this object is linked to.
    Whenever the set is modified, the modification will affect this ontology
    individual."""

    # Public API
    # ↓ ------ ↓

    @property
    def individual(self) -> OntologyIndividual:
        """Ontology individual that this set refers to."""
        return self._individual

    @property
    def predicate(self) -> OntologyPredicate:
        """Predicate that this set refers to."""
        return self._predicate

    def __repr__(self) -> str:
        """Return repr(self)."""
        return (
            set(self).__repr__()
            + " <"
            + (f"{self._predicate} " if self._predicate is not None else "")
            + f"of ontology individual {self._individual}>"
        )

    def one(
        self,
    ) -> Union[AnnotationValue, AttributeValue, RelationshipValue]:
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
            raise ResultEmptyError(
                f"No elements attached to "
                f"{self._individual} through "
                f"{self._predicate}."
            )
        second_element = next(iter_self, StopIteration)
        if second_element is not StopIteration:
            raise MultipleResultsError(
                f"More than one element attached "
                f"to {self._individual} through "
                f"{self._predicate}."
            )
        return first_element

    def any(
        self,
    ) -> Optional[Union[AnnotationValue, AttributeValue, RelationshipValue]]:
        """Return any element of the set.

        Returns:
            Any element from the set if the set is not empty, else None.
        """
        return next(iter(self), None)

    def all(self) -> ObjectSet:
        """Return all elements from the set.

        Returns:
            All elements from the set, namely the set itself.
        """
        return self

    # ↑ ------ ↑
    # Public API

    @property
    def _predicates(
        self,
    ) -> Optional[
        Union[
            Set[OntologyAttribute],
            Set[OntologyRelationship],
            Set[OntologyAnnotation],
        ]
    ]:
        """All the predicates to which this instance refers to.

        Returns:
            Such predicates, or `None` if no main predicate is
            associated with this `ObjectSet`.
        """
        return set(
            self._predicate.subclasses if self._predicate is not None else None
        )

    def __init__(
        self,
        predicate: Optional[OntologyPredicate],
        individual: OntologyIndividual,
    ):
        """Fix the linked predicate and CUDS object."""
        self._individual = individual
        self._predicate = predicate
        super().__init__()


class AttributeSet(ObjectSet):
    """A set interface to an ontology individual's attributes.

    This class looks like and acts like the standard `set`, but it is an
    interface to the methods from `OntologyIndividual` that manage the
    attributes.
    """

    # Public API
    # ↓ ------ ↓

    def __iter__(self) -> Iterator[AttributeValue]:
        """The values assigned to the referred predicates.

        Such predicates are the main attribute and its subclasses.

        Returns:
            The mentioned values.
        """
        yielded: Set[AttributeValue] = set()
        for value in chain(
            *(
                self._individual.attributes_value_generator(
                    attribute=attribute
                )
                for attribute in self._predicates
            )
        ):
            if value not in yielded:
                yielded.add(value)
                yield value

    def __contains__(self, item: AttributeValue) -> bool:
        """Check whether a value is assigned to the set's attribute."""
        return any(
            self._individual.attributes_value_contains(attribute, item)
            for attribute in self._predicates
        )

    def update(self, other: Iterable[AttributeValue]) -> None:
        """Update the set with the union of itself and others."""
        underlying_set = set(self)
        added = set(other).difference(underlying_set)
        self._individual.attributes_add(self._predicate, added)

    def intersection_update(self, other: Iterable[AttributeValue]) -> None:
        """Update the set with the intersection of itself and another."""
        underlying_set = set(self)
        intersection = underlying_set.intersection(other)
        removed = underlying_set.difference(intersection)
        for attribute in self._predicates:
            self._individual.attributes_delete(attribute, removed)

    def difference_update(self, other: Iterable[AttributeValue]) -> None:
        """Remove all elements of another set from this set."""
        removed = set(self) & set(other)
        for attribute in self._predicates:
            self._individual.attributes_delete(attribute, removed)

    def symmetric_difference_update(self, other: Set[AttributeValue]) -> None:
        """Update set with the symmetric difference of it and another."""
        underlying_set = set(self)
        symmetric_difference = underlying_set.symmetric_difference(other)
        added = symmetric_difference.difference(underlying_set)
        self._individual.attributes_add(self._predicate, added)
        removed = underlying_set.difference(symmetric_difference)
        for attribute in self._predicates:
            self._individual.attributes_delete(attribute, removed)

    # ↑ ------ ↑
    # Public API

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
            predicates = set(self._individual.attributes_generator())
            # The code below is technically true, but makes no
            #  difference due to how `attributes_generator` is written.
            # predicates = set(chain(
            #    subclasses
            #    for attributes in
            #    self._individual.attributes_generator(_notify_read=True)
            #    for subclasses in attributes.subclasses
            # ))
        return predicates

    def __init__(
        self,
        attribute: Optional[OntologyAttribute],
        individual: OntologyIndividual,
    ):
        """Fix the liked OntologyAttribute and ontology individual."""
        super().__init__(attribute, individual)


class RelationshipSet(ObjectSet):
    """A set interface to an ontology individual's relationships.

    This class looks like and acts like the standard `set`, but it is an
    interface to the methods from `OntologyIndividual` that manage the
    relationships.
    """

    @staticmethod
    def prevent_class_filtering(func):
        """Decorator breaking methods when class filtering is enabled."""

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self._class_filter is not None:
                raise RuntimeError(
                    "Cannot edit a set with a class filter in-place."
                )
            return func(self, *args, **kwargs)

        return wrapper

    # Bind static method to use as decorator.
    prevent_class_filtering = prevent_class_filtering.__get__(object, None)

    # Public API
    # ↓ ------ ↓

    def __iter__(self) -> Iterator[OntologyIndividual]:
        """Iterate over individuals assigned to `self._predicates`.

        Note: no class filter.

        Returns:
            The mentioned underlying set.
        """
        individual = self._individual.identifier
        graph = self._individual.session.graph
        ontology = self._individual.session.ontology
        predicates = self._predicates

        # Get the predicate IRIs to be considered.
        predicates_direct = {predicate.identifier for predicate in predicates}
        predicates_inverse = {
            p.identifier
            for predicate in predicates
            for p in (predicate.inverse,)
            if p is not None
        }
        if self._inverse:
            predicates_direct, predicates_inverse = (
                predicates_inverse,
                predicates_direct,
            )

        # Get the identifiers of the individuals connected to
        # `self._individual` through the allowed predicates.
        connected = set()
        triples = graph.triples((individual, None, None))
        connected |= {o for s, p, o in triples if p in predicates_direct}
        triples = graph.triples((None, None, individual))
        connected |= {s for s, p, o in triples if p in predicates_inverse}
        identifiers = (
            tuple(uid.to_identifier() for uid in self._uid_filter)
            if self._uid_filter
            else tuple()
        )
        if identifiers:
            connected &= set(identifiers)
        if self._class_filter:
            connected &= {
                identifier
                for identifier in connected
                if self._class_filter
                in (
                    subclass
                    for c in graph.objects(identifier, RDF_type)
                    for subclass in ontology.from_identifier_typed(
                        c, typing=OntologyClass
                    ).superclasses
                )
            }

        if self._uid_filter:
            yield from (
                self._individual.session.from_identifier_typed(
                    identifier, typing=OntologyIndividual
                )
                if identifier in connected
                else None
                for identifier in identifiers
            )
        else:
            for identifier in connected:
                try:
                    yield self._individual.session.from_identifier_typed(
                        identifier, typing=OntologyIndividual
                    )
                except KeyError:
                    logger.warning(
                        f"Ignoring identifier {identifier}, which does not "
                        f"match an ontology individual belonging to a class "
                        f"in the ontology."
                    )

    def __contains__(self, item: OntologyIndividual) -> bool:
        """Check if an individual is connected via set's relationship."""
        if item not in self.individual.session:
            return False

        original_uid_filter = self._uid_filter
        try:
            self._uid_filter = (item.uid,)
            return next(iter(self)) is not None
        finally:
            self._uid_filter = original_uid_filter

    def __invert__(self) -> RelationshipSet:
        """Get the inverse RelationshipSet."""
        return self.inverse

    @property
    def inverse(self) -> RelationshipSet:
        """Get the inverse RelationshipSet.

        Returns a RelationshipSet that works in the inverse direction: the
        ontology individuals displayed are the ones which are the subject of
        the relationship.
        """
        return RelationshipSet(
            relationship=self._predicate,
            individual=self.individual,
            oclass=self._class_filter,
            inverse=not self._inverse,
        )

    @prevent_class_filtering
    def update(self, other: Iterable[OntologyIndividual]) -> None:
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
            self._connect(individual, rel=self._predicate)

    @prevent_class_filtering
    def intersection_update(self, other: Iterable[OntologyIndividual]) -> None:
        """Update the set with the intersection of itself and another."""
        # Note: please read the comment on the `update` method.
        underlying_set = set(self)
        result = underlying_set.intersection(other)

        removed = underlying_set.difference(result)
        if removed:
            for rel in self._predicates:
                self._disconnect(*removed, rel=rel)

        added = result.difference(underlying_set)
        self._connect(*added, rel=self._predicate)

    @prevent_class_filtering
    def difference_update(self, other: Iterable[OntologyIndividual]) -> None:
        """Remove all elements of another set from this set."""
        # Note: please read the comment on the `update` method.
        removed = set(self) & set(other)
        if removed:
            for rel in self._predicates:
                self._disconnect(*removed, rel=rel)

    @prevent_class_filtering
    def symmetric_difference_update(
        self, other: Iterable[OntologyIndividual]
    ) -> None:
        """Update with the symmetric difference of it and another."""
        # Note: please read the comment on the `update` method.
        underlying_set = set(self)
        result = underlying_set.symmetric_difference(other)

        removed = underlying_set.difference(result)
        if removed:
            for rel in self._predicates:
                self._disconnect(*removed, rel=rel)

        added = result.difference(underlying_set)
        self._connect(*added, rel=self._predicate)

    @prevent_class_filtering
    def _connect(
        self,
        *individuals: OntologyIndividual,
        rel: Optional[OntologyRelationship] = None,
    ):
        individuals = set(individuals)

        # Raise exception if any of the individuals to connect belongs to a
        # different session.
        different_session = {
            individual
            for individual in individuals
            if individual not in self.individual.session
        }
        if different_session:
            raise RuntimeError(
                f"Cannot connect ontology individuals belonging to a "
                f"different session: "
                f"{','.join(str(i) for i in different_session)}."
                f"Please add them to this session first using `session.add`."
            )

        rel = rel or self.predicate
        # Raise exception for predicates that are not a subclass of the
        # RelationshipSet's ontology predicates.
        if rel != self.predicate:
            allowed = (
                self._predicates if self.predicate is not None else {None}
            )
            if rel not in allowed:
                raise RuntimeError(
                    f"Predicate {rel} not within the set of allowed "
                    f"predicates {allowed}."
                )
        if rel is None:
            raise RuntimeError("No predicate specified.")
        rel = rel.identifier

        for individual in individuals:
            self.individual.session.graph.add(
                (self.individual.identifier, rel, individual.identifier)
            )

    @prevent_class_filtering
    def _disconnect(
        self,
        *individuals: OntologyIndividual,
        rel: Optional[OntologyRelationship] = None,
    ):
        individuals = set(individuals)

        # Raise exception if any of the individuals to connect belongs to a
        # different session.
        different_session = {
            individual
            for individual in individuals
            if individual not in self.individual.session
        }
        if different_session:
            raise RuntimeError(
                f"Cannot disconnect ontology individuals belonging to a "
                f"different session: "
                f"{','.join(str(i) for i in different_session)}."
                f"Please add them to this session first using `session.add`."
            )

        rel = rel or self.predicate
        # Raise exception for predicates that are not a subclass of the
        # RelationshipSet's ontology predicates.
        if rel != self.predicate:
            allowed = (
                self._predicates if self.predicate is not None else {None}
            )
            if rel not in allowed:
                raise RuntimeError(
                    f"Predicate {rel} not within the set of allowed "
                    f"predicates {allowed}"
                )
        if rel is None:
            raise RuntimeError("No predicate specified.")

        for rel in rel.subclasses:
            for individual in individuals:
                self.individual.session.graph.remove(
                    (
                        self.individual.identifier,
                        rel.identifier,
                        individual.identifier,
                    )
                )

    # ↑ ------ ↑
    # Public API

    _predicate: Optional[OntologyRelationship]
    _class_filter: Optional[OntologyClass]
    _uid_filter: Optional[Tuple[UID]]
    _inverse: bool = False

    def __init__(
        self,
        relationship: Optional[OntologyRelationship],
        individual: OntologyIndividual,
        oclass: Optional[OntologyClass] = None,
        inverse: bool = False,
        uids: Optional[Iterable[UID]] = None,
    ):
        """Fix the liked OntologyRelationship and ontology individual."""
        if relationship is not None and not isinstance(
            relationship, OntologyRelationship
        ):
            raise TypeError(
                "Found object of type %s. "
                "Should be an OntologyRelationship." % type(relationship)
            )
        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError(
                "Found object of type %s. Should be "
                "an OntologyClass." % type(oclass)
            )
        uids = tuple(uids) if uids is not None else None
        if uids is not None:
            for uid in uids:
                if not isinstance(uid, UID):
                    raise TypeError(
                        "Found object of type %s. Should be an UID."
                        % type(uid)
                    )

        self._class_filter = oclass
        self._inverse = inverse
        self._uid_filter = uids
        super().__init__(relationship, individual)

    def iter_low_level(
        self,
    ) -> Union[
        Iterator[Tuple[Node, Optional[Node], Optional[bool]]],
        Iterator[Tuple[Node, Optional[Node], Optional[bool], Node]],
    ]:
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
        direct_allowed = {p.identifier for p in self._predicates}
        inverse_allowed = {
            rel.identifier
            for rel in filter(None, (p.inverse for p in self._predicates))
        }
        if self._inverse:
            direct_allowed, inverse_allowed = inverse_allowed, direct_allowed

        # Get the individuals connected to `self._individual` through the
        # allowed predicates, that is, o and s from the last comment.
        individual = self._individual.identifier
        graph = self._individual.session.graph
        if self._uid_filter is None:
            predicate_individual_direct = (
                (o, p)
                for p in direct_allowed
                for o in graph.objects(individual, p)
            )
            predicate_individual_inverse = (
                (s, p)
                for p in inverse_allowed
                for s in graph.subjects(p, individual)
            )
            individuals_and_relationships = chain(
                ((o, p, True) for o, p in predicate_individual_direct),
                ((s, p, False) for s, p in predicate_individual_inverse),
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
                        (
                            (p, True)
                            for p in direct_allowed
                            if (individual, p, identifier) in graph
                        ),
                        (
                            (p, False)
                            for p in inverse_allowed
                            if (identifier, p, individual) in graph
                        ),
                    )
                    first = next(found, (None, None))
                    yield tuple((identifier, *first))
                    if first != (None, None):
                        yield from ((identifier, *f) for f in found)

            individuals_and_relationships = individuals_and_relationships()

        yield from individuals_and_relationships


class AnnotationSet(ObjectSet):
    """A set interface to an ontology individual's annotations.

    This class looks like and acts like the standard `set`, but it is an
    interface to the methods from `OntologyIndividual` that manage the
    annotations.
    """

    _predicate: OntologyAnnotation

    def __init__(
        self,
        annotation: Optional[OntologyAnnotation],
        individual: OntologyIndividual,
    ) -> None:
        """Fix the linked OntologyAnnotation and ontology individual."""
        super().__init__(annotation, individual)

    # Public API
    # ↓ ------ ↓

    def __iter__(self) -> Iterator[AnnotationValue]:
        """Iterate over annotations linked to the individual."""
        yield from self._individual.annotations_value_generator(
            annotation=self._predicate
        )

    def __contains__(self, item) -> bool:
        """Determine whether the individual is annotated with an item."""
        return super().__contains__(item)

    def update(self, other: Iterable[AnnotationValue]) -> None:
        """Update the set with the union of itself and other."""
        self._individual.annotations_add(
            annotation=self._predicate, values=other
        )

    def intersection_update(self, other: Iterable[AnnotationValue]) -> None:
        """Update the set with the intersection of itself and another."""
        self._individual.annotations_set(
            annotation=self._predicate, values=other
        )

    def difference_update(self, other: Iterable[Any]) -> None:
        """Return self-=other."""
        self._individual.annotations_delete(
            annotation=self._predicate, values=set(self) & set(other)
        )

    def symmetric_difference_update(
        self, other: Iterable[AnnotationValue]
    ) -> None:
        """Return self^=other."""
        self._individual.annotations_set(
            self._predicate, set(self) ^ set(other)
        )

    # ↑ ------ ↑
    # Public API


class OntologyIndividual(OntologyEntity):
    """An ontology individual."""

    rdf_identifier = Identifier

    def __init__(
        self,
        uid: Optional[UID] = None,
        session: Optional[Session] = None,
        triples: Optional[Iterable[Triple]] = None,
        merge: bool = False,
        class_: Optional[OntologyClass] = None,
        attributes: Optional[
            Mapping[OntologyAttribute, Iterable[AttributeValue]]
        ] = None,
    ) -> None:
        """Initialize the ontology individual."""
        if uid is None:
            uid = UID()
        elif not isinstance(uid, UID):
            raise Exception(
                f"Tried to initialize an ontology individual with "
                f"uid {uid}, which is not a UID object."
            )
        triples = set(triples) if triples is not None else set()
        # Attribute triples.
        attributes = attributes or dict()
        triples |= {
            (
                uid.to_iri(),
                k.iri,
                Literal(k.convert_to_datatype(e), datatype=k.datatype),
            )
            for k, v in attributes.items()
            for e in v
        }
        # Class triples.
        if class_:
            triples |= {(uid.to_iri(), RDF.type, class_.iri)}

        super().__init__(uid, session, triples or None, merge=merge)

    # Public API
    # ↓ ------ ↓

    @property
    def classes(self) -> FrozenSet[OntologyClass]:
        """Get the ontology classes of this ontology individual.

        This property is writable. The classes that an ontology individual
        belongs to can be changed writing the desired values to this property.

        Returns:
            A set with all the ontology classes of the ontology
            individual. When the individual has no classes, the set is empty.
        """
        return frozenset(
            self.session.ontology.from_identifier_typed(
                o, typing=OntologyClass
            )
            for o in self.session.graph.objects(self.identifier, RDF_type)
        )

    @classes.setter
    def classes(self, value: Iterable[OntologyClass]) -> None:
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

    def is_a(self, ontology_class: OntologyClass) -> bool:
        """Check if the individual is an instance of the given ontology class.

        Args:
            ontology_class: The ontology class to test against.

        Returns:
            Whether the ontology individual is an instance of such ontology
            class.
        """
        return self.is_subclass_of(ontology_class)

    def __dir__(self) -> Iterable[str]:
        """Show the individual's attributes as autocompletion suggestions.

        This method takes care of the autocompletion for the dot notation.
        """
        attribute_autocompletion = filter(
            lambda x: x.isidentifier(), self._attribute_autocompletion()
        )
        return chain(super().__dir__(), attribute_autocompletion)

    def _ipython_key_completions_(self):
        """Show the individual's predicates as tab completion suggestions.

        The predicates include its attributes, relationships and annotations.

        This method is specific for the bracket notation ([], __getitem__).
        """
        return chain(
            super().__dir__(),
            self._attribute_autocompletion(),
            self._relationship_autocompletion(),
            self._annotation_autocompletion(),
        )

    def __getattr__(self, name: str) -> AttributeSet:
        """Retrieve the value of an attribute of the individual.

        Args:
            name: The label or suffix of the attribute.

        Raises:
            AttributeError: Unknown attribute label or suffix.
            AttributeError: Multiple attributes for the given label or suffix.

        Returns:
            The value of the attribute (a python object).
        """
        attributes = self._attributes_get_by_name(name)
        num_attributes = len(attributes)
        if num_attributes == 0:
            raise AttributeError(
                f"No attribute associated with {self} with label or prefix "
                f"{name} found."
            )
        elif num_attributes >= 2:
            error = (
                f"There are multiple attributes with label or suffix {name} "
                f"associated with {self}:"
                f" {', '.join(r.iri for r in attributes)}. "
                f"Please use an OntologyAttribute object together with the "
                f"indexing notation `individual[attribute]` to access the "
                f"values of this attribute."
            )
            raise AttributeError(error)
        attr = attributes.pop()

        values = self.attributes_value_generator(attr)
        value = next(values, None)
        if next(values, None) is not None:
            raise RuntimeError(
                f"Tried to fetch values of a "
                f"non-functional attribute {attr} using "
                f"the dot notation. This is not "
                f"supported. "
                f"\n \n"
                f"Please use subscript "
                f"notation instead for such attributes: "
                f"my_cuds[{attr}]. This will return a set "
                f"of values instead of a single one"
            )
        return value

    def __setattr__(
        self,
        name: str,
        value: Optional[Union[AttributeValue, Set[AttributeValue]]],
    ) -> None:
        """Set the value(s) of an attribute.

        Args:
            name: The label or suffix of the attribute.
            value: The new value(s).

        Raises:
            AttributeError: Unknown attribute label or suffix.
            AttributeError: Multiple attributes for the given label or suffix.
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        try:
            attributes = self._attributes_get_by_name(name)
            num_attributes = len(attributes)
            if num_attributes == 0:
                raise AttributeError(
                    f"No attribute, associated with {self} with label or"
                    f"prefix {name} found."
                )
            elif num_attributes >= 2:
                error = (
                    f"There are multiple attributes with label or suffix "
                    f"{name} associated with {self}:"
                    f" {', '.join(r.iri for r in attributes)}. "
                    f"Please use an OntologyAttribute object together with the"
                    f" indexing notation `individual[attribute]` to access "
                    f"the values of this attribute."
                )
                raise AttributeError(error)
            attr = attributes.pop()
            value = {value} if value is not None else set()
            self.attributes_set(attr, value)
        except AttributeError as e:
            # Might still be an attribute of a subclass of OntologyIndividual.
            if hasattr(self, name):
                super().__setattr__(name, value)
            else:
                raise e

    def __getitem__(
        self, rel: Union[OntologyPredicate, str]
    ) -> Union[AttributeSet, RelationshipSet, AnnotationSet]:
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
        - When `rel` is a string, the string is resolved to an
          OntologyAttribute, OntologyRelationship or OntologyAnnotation with a
          matching label, and then one of the cases above applies.

        The reason why a set is returned and not a list, or any other
        container allowing repeated elements, is that the underlying RDF
        graph does not accept duplicate statements.

        Args:
            rel: An ontology attribute, an ontology relationship or an ontology
                annotation (OWL datatype property, OWL object property,
                OWL annotation property). Alternatively a string, which will be
                resolved, using labels, to one of the classes described above.

        Raises:
            KeyError: Unknown attribute, relationship or annotation label or
                suffix.
            KeyError: Multiple attributes, relationships or annotations found
                for the given label or suffix.
            TypeError: Trying to use something that is neither an
                OntologyAttribute, an OntologyRelationship, an
                OntologyAnnotation or a string as index.
        """
        if isinstance(rel, str):
            """Resolve string to an attribute, relationship or annotation."""
            entities = set()

            # Try to find a matching attribute.
            try:
                entities |= self._attributes_get_by_name(rel)
            except AttributeError:
                pass

            # Try to find a matching relationship.
            entities |= {
                relationship
                for _, relationship in self.relationships_iter(return_rel=True)
                for label in relationship.iter_labels(return_literal=False)
                if rel == label or relationship.iri.endswith(rel)
            }

            # Try to find a matching annotation.
            entities |= {
                annotation
                for _, annotation in self.annotations_iter(return_rel=True)
                for label in annotation.iter_labels(
                    return_literal=False, return_prop=False
                )
                if rel == label or annotation.iri.endswith(rel)
            }

            num_entities = len(entities)
            if num_entities == 0:
                raise KeyError(
                    f"No attribute, relationship or annotation "
                    f"associated with {self} with label or suffix {rel} found."
                )
            elif num_entities >= 2:
                raise KeyError(
                    f"There are multiple attributes, relationships or "
                    f"annotations with label or suffix {rel} associated with "
                    f"{self}:"
                    f"{', '.join(r.iri for r in entities)}. "
                    f"Please use an OntologyAttribute, OntologyRelationship "
                    f"or OntologyAnnotation object together with the "
                    f"indexing notation `individual[entity]` to access the "
                    f"values of this attribute, relationship or annotation."
                )
            rel = entities.pop()

        if isinstance(rel, OntologyAttribute):
            set_class = AttributeSet
        elif isinstance(rel, OntologyRelationship):
            set_class = RelationshipSet
        elif isinstance(rel, OntologyAnnotation):
            set_class = AnnotationSet
        else:
            raise TypeError(
                f"Ontology individual indices must be ontology "
                f"relationships, ontology attributes, "
                f"or ontology annotations, not {type(rel)}."
            )
        return set_class(rel, self)

    def __setitem__(
        self,
        rel: Union[OntologyPredicate, str],
        values: Optional[Union[PredicateValue, Iterable[PredicateValue]]],
    ) -> None:
        """Manages object, data and annotation properties.

        The subscripting syntax `individual[rel] = ` allows,

        - When `rel` is an OntologyRelationship, to replace the list of
          ontology individuals that are connected to `individual` through rel.
        - When `rel` is an OntologyAttribute, to replace the values of
          such attribute.
        - When `rel` is an OntologyAnnotation, to replace the annotation
          values of such annotation property.
        - When `rel` is a string, the string is resolved to an
          OntologyAttribute, OntologyRelationship or OntologyAnnotation with a
          matching label, and then one of the cases above applies.

        This function only accepts hashable objects as input, as the
        underlying RDF graph does not accept duplicate statements.

        Args:
            rel: Either an ontology attribute, an ontology relationship or
                an ontology annotation (OWL datatype property, OWL object
                property, OWL annotation property). Alternatively a string,
                which will be resolved, using labels, to one of the classes
                described above.
            values: Either a single element compatible with the OWL standard
                (this includes ontology individuals) or a set of such
                elements.

        Raises:
            KeyError: Unknown attribute, relationship or annotation label or
                suffix.
            KeyError: Multiple attributes, relationships or annotations found
                for the given label or suffix.
            TypeError: Trying to assign attributes using an object property,
                trying to assign ontology individuals using a data property,
                trying to use something that is neither an OntologyAttribute,
                an OntologyRelationship, an OntologyAnnotation nor a string as
                index.
        """
        if (
            isinstance(values, ObjectSet)
            and values.individual is self
            and values.predicate is rel
        ):
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
        values = (
            {values}
            if not isinstance(values, (Tuple, Set, MutableSet))
            else set(values)
        )
        # Apparently instances of MutableSet are not instances of Set.

        # Classify the values by type.
        values = self._classify_by_type(values)

        if isinstance(rel, str):
            """Resolve string to an attribute, relationship or annotation."""
            entities = set()

            # Try to find a matching attribute.
            try:
                entities |= self._attributes_get_by_name(rel)
            except AttributeError:
                pass

            # Try to find a matching relationship.
            entities |= {
                relationship
                for _, relationship in self.relationships_iter(return_rel=True)
                for label in relationship.iter_labels(return_literal=False)
                if rel == label or relationship.iri.endswith(rel)
            }

            # Try to find a matching annotation.
            entities |= {
                annotation
                for _, annotation in self.annotations_iter(return_rel=True)
                for label in annotation.iter_labels(
                    return_literal=False, return_prop=False
                )
                if rel == label or annotation.iri.endswith(rel)
            }

            num_entities = len(entities)
            if num_entities == 0:
                raise KeyError(
                    f"No attribute, relationship or annotation "
                    f"associated with {self} with label or suffix {rel} found."
                )
            elif num_entities >= 2:
                raise KeyError(
                    f"There are multiple attributes, relationships or "
                    f"annotations with label or suffix {rel} associated with "
                    f"{self}:"
                    f"{', '.join(r.iri for r in entities)}. "
                    f"Please use an OntologyAttribute, OntologyRelationship "
                    f"or OntologyAnnotation object together with the "
                    f"indexing notation `individual[entity]` to access the "
                    f"values of this attribute, relationship or annotation."
                )
            rel = entities.pop()

        # Perform assignments.
        if isinstance(rel, OntologyRelationship):
            if (len(values) > 0 and OntologyIndividual not in values) or len(
                values
            ) > 1:
                raise TypeError(
                    f"Trying to assign python objects which are "
                    f"not ontology individuals using an object "
                    f"property {rel}."
                )
            assigned = set(values.get(OntologyIndividual, set()))
            current = RelationshipSet(rel, self, oclass=None)

            add = assigned - current
            remove = current - assigned

            current -= remove
            current |= add
        elif isinstance(rel, OntologyAttribute):
            if (
                len(values) > 0
                and all(
                    x not in values for x in (ATTRIBUTE_VALUE_TYPES, Literal)
                )
            ) or len(values) > 2:
                raise TypeError(
                    f"Trying to assign python objects which "
                    f"cannot be interpreted as literals "
                    f"using a data property {rel}."
                )
            assigned = set(values.get(ATTRIBUTE_VALUE_TYPES, set())) | set(
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
            raise TypeError(
                f"Ontology individual indices must be ontology "
                f"relationships, ontology attributes or ontology "
                f"annotations not {type(rel)}."
            )

    def __delitem__(self, rel: OntologyPredicate):
        """Delete all objects attached through the given predicate.

        Args:
            rel: Either an ontology attribute, an ontology relationship or
                an ontology annotation (OWL datatype property, OWL object
                property, OWL annotation property). Alternatively a string,
                which will be resolved, using labels, to one of the classes
                described above.
        """
        self.__setitem__(rel=rel, values=set())

    def connect(
        self,
        *individuals: Union[OntologyIndividual, Identifier, str],
        rel: Union[OntologyRelationship, Identifier],
    ) -> None:
        """Connect ontology individuals to other ontology individuals.

        Args:
            individuals: The individuals to be connected. Their identifiers may
                also be used.
            rel: The relationship between the objects.

        Raises:
            TypeError: Objects that are not ontology individuals,
                identifiers or strings provided as positional arguments.
            TypeError: Object that is not an ontology relationship or the
                identifier of an ontology relationship passed as keyword
                argument `rel`.
            RuntimeError: Ontology individuals that belong to a different
                session provided.
        """
        individuals = list(individuals)
        for i, x in enumerate(individuals):
            if isinstance(x, str):
                if not isinstance(x, Identifier):
                    x = URIRef(x)
                x = self.session.from_identifier_typed(
                    x, typing=OntologyIndividual
                )
                individuals[i] = x
            if not isinstance(x, OntologyIndividual):
                raise TypeError(
                    f"Expected {OntologyIndividual}, {Identifier} or {str} "
                    f"objects, not {type(x)}."
                )
        individuals = set(individuals)

        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier_typed(
                rel,
                typing=OntologyRelationship,
            )
        elif not isinstance(rel, OntologyRelationship):
            raise TypeError(
                "Found object of type %s passed to argument rel. "
                "Should be an OntologyRelationship." % type(rel)
            )

        self[rel] |= individuals

    def disconnect(
        self,
        *individuals: Union[OntologyIndividual, Identifier, str],
        rel: Union[OntologyRelationship, Identifier] = OWL.topObjectProperty,
        oclass: Optional[OntologyClass] = None,
    ) -> None:
        """Disconnect ontology individuals from this one.

        Args:
            individuals: Specify the individuals to disconnect. When no
                individuals are specified, all connected individuals are
                considered.
            rel: Only remove individuals which are connected by subclass of the
                given relationship. Defaults to OWL.topObjectProperty (any
                relationship).
            oclass: Only remove elements which are a subclass of the given
                ontology class. Defaults to None (no filter).

        Raises:
            TypeError: Objects that are not ontology individuals,
                identifiers or strings provided as positional arguments.
            TypeError: Object that is not an ontology relationship or the
                identifier of an ontology relationship passed as keyword
                argument `rel`.
            TypeError: Object that is not an ontology class passed as
                keyword argument `oclass`.
            RuntimeError: Ontology individuals that belong to a different
                session provided.
        """
        individuals = list(individuals)
        for i, x in enumerate(individuals):
            if isinstance(x, str):
                if not isinstance(x, Identifier):
                    x = URIRef(x)
                x = self.session.from_identifier_typed(
                    x, typing=OntologyIndividual
                )
                individuals[i] = x
            if not isinstance(x, OntologyIndividual):
                raise TypeError(
                    f"Expected {OntologyIndividual}, {Identifier} or {str} "
                    f"objects, not {type(x)}."
                )
        individuals = set(individuals)

        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier_typed(
                rel, typing=OntologyRelationship
            )
        elif not isinstance(rel, OntologyRelationship):
            raise TypeError(
                "Found object of type %s passed to argument rel. "
                "Should be an OntologyRelationship." % type(rel)
            )

        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError(
                "Found object of type %s passed to argument "
                "oclass. Should be an OntologyClass." % type(oclass)
            )

        individuals = individuals or self[rel]

        if oclass:
            individuals = {x for x in individuals if x.is_a(oclass)}

        self[rel] -= individuals

    def get(
        self,
        *individuals: Union[OntologyIndividual, Identifier, str],
        rel: Union[OntologyRelationship, Identifier] = OWL.topObjectProperty,
        oclass: Optional[OntologyClass] = None,
        return_rel: bool = False,
    ) -> Union[
        RelationshipSet,
        Optional[OntologyIndividual],
        Tuple[Optional[OntologyIndividual], ...],
        Tuple[Tuple[OntologyIndividual, OntologyRelationship]],
    ]:
        """Return the connected individuals.

        The structure of the output can vary depending on the form used for
        the call. See the "Returns:" section of this
        docstring for more details on this.

        Note: If you are reading the SimPhoNy documentation API Reference, it
        is likely that you cannot read this docstring. As a workaround, click
        the `source` button to read it in its raw form.

        Args:
            individuals: Restrict the elements to be returned to a certain
                subset of the connected elements.
            rel: Only return individuals which are connected by a subclass
                of the given relationship. Defaults to
                OWL.topObjectProperty (any relationship).
            oclass: Only yield individuals which are a subclass of the given
                ontology class. Defaults to None (no filter).
            return_rel: Whether to return the connecting relationship.
                Defaults to False.

        Returns:
            Calls without `*individuals` (RelationshipSet): The result of the
                call is a set-like object. This corresponds to
                the calls `get()`, `get(rel=___)`, `get(oclass=___)`,
                `get(rel=___, oclass=___)`, with the parameter `return_rel`
                unset or set to False.
            Calls with `*individuals` (Optional[OntologyIndividual],
                    Tuple[Optional["OntologyIndividual"], ...]):
                The position of each element in the result is determined by
                the position of the corresponding identifier/individual in the
                given list of identifiers/individuals. In this case, the result
                can contain `None` values if a given identifier/individual is
                not connected to this individual, or if it does not satisfy
                the class filter. When only one individual or identifier is
                specified, a single object is returned instead of a Tuple.
                This description corresponds to the calls `get(*individuals)`,
                `get(*individuals, rel=___)`,
                `get(*individuals, rel=___, oclass=___)`, with the parameter
                `return_rel` unset or set to False.
            Calls with `return_rel=True` (Tuple[
                    Tuple[OntologyIndividual, OntologyRelationship]]):
                The dependence of the order of the elements is maintained
                for the calls with `*individuals`, a non-deterministic order is
                used for the calls without `*individuals`. No `None` values
                are contained in the result (such identifiers or individuals
                are simply skipped). Moreover, the elements returned are now
                pairs of individuals and the relationship connecting this
                individual to such ones. This description corresponds to any
                call of the form `get(..., return_rel=True)`.

        Raises:
            TypeError: Objects that are not ontology individuals,
                identifiers or strings provided as positional arguments.
            TypeError: Object that is not an ontology relationship or the
                identifier of an ontology relationship passed as keyword
                argument `rel`.
            TypeError: Object that is not an ontology class passed as
                keyword argument `oclass`.
            RuntimeError: Ontology individuals that belong to a different
                session provided.
        """
        identifiers = list(individuals)
        for i, x in enumerate(identifiers):
            if not isinstance(x, (OntologyIndividual, Identifier, str)):
                raise TypeError(
                    f"Expected {OntologyIndividual}, {Identifier} or {str} "
                    f"objects, not {type(x)}."
                )
            elif isinstance(x, OntologyIndividual) and x not in self.session:
                raise RuntimeError(
                    "Cannot get an individual that belongs to "
                    "a different session, please add it to this session "
                    "first using `session.add`."
                )

            if isinstance(x, str):
                if not isinstance(x, Identifier):
                    x = URIRef(x)
                identifiers[i] = UID(x)
            elif isinstance(x, OntologyIndividual):
                identifiers[i] = UID(x.identifier)

        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier_typed(
                rel, typing=OntologyRelationship
            )
        elif not isinstance(rel, OntologyRelationship):
            raise TypeError(
                "Found object of type %s passed to argument rel. "
                "Should be an OntologyRelationship." % type(rel)
            )

        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError(
                "Found object of type %s passed to argument "
                "oclass. Should be an OntologyClass." % type(oclass)
            )

        relationship_set = RelationshipSet(
            rel, self, oclass=oclass, uids=tuple(identifiers) or None
        )

        if not return_rel:
            if not identifiers:
                return relationship_set
            else:
                return (
                    next(iter(relationship_set), None)
                    if len(identifiers) <= 1
                    else tuple(relationship_set)
                )
        else:
            result = []
            for (i, r, t) in relationship_set.iter_low_level():
                if not t:
                    continue
                session = self.session
                result += [
                    (
                        session.from_identifier_typed(
                            i, typing=OntologyIndividual
                        ),
                        session.ontology.from_identifier_typed(
                            r, typing=OntologyRelationship
                        ),
                    )
                ]
            return tuple(result)

    def iter(
        self,
        *individuals: Union[OntologyIndividual, Identifier, str],
        rel: Union[OntologyRelationship, Identifier] = OWL.topObjectProperty,
        oclass: Optional[OntologyClass] = None,
        return_rel: bool = False,
    ) -> Union[
        Iterator[OntologyIndividual],
        Iterator[Optional[OntologyIndividual]],
        Iterator[Tuple[OntologyIndividual, OntologyRelationship]],
    ]:
        """Iterate over the connected individuals.

        The structure of the output can vary depending on the form used for
        the call. See the "Returns:" section of this docstring for more
        details on this.

        Note: If you are reading the SimPhoNy documentation API Reference, it
        is likely that you cannot read this docstring. As a workaround, click
        the `source` button to read it in its raw form.

        Args:
            individuals: Restrict the elements to be returned to a certain
                subset of the connected elements.
            rel: Only yield individuals which are connected by a subclass
                of the given relationship. Defaults to
                OWL.topObjectProperty (any relationship).
            oclass: Only yield individuals which are a subclass of the given
                ontology class. Defaults to None (no filter).
            return_rel: Whether to yield the connecting relationship.
                Defaults to False.

        Returns:
            Calls without `*individuals` (Iterator[OntologyIndividual]): The
                position of each element in the result is non-deterministic.
                This corresponds to the calls `iter()`, `iter(rel=___)`,
                `iter(oclass=___)`, `iter(rel=___, oclass=___)`, with the
                parameter `return_rel` unset or set to False.
            Calls with `*individuals` (Iterator[Optional[
                    OntologyIndividual]]):
                The position of each element in the result is determined by the
                position of the corresponding identifier/individual in the
                given list of identifiers/individuals. In this case, the result
                can contain `None` values if a given identifier/individual is
                not connected to this individual, or if it does not satisfy
                the class filter. This description corresponds to the calls
                `iter(*individuals)`, `iter(*individuals, rel=___)`,
                `iter(*individuals, rel=___, oclass=`___`)`.
            Calls with `return_rel=True` (Iterator[
                    Tuple[OntologyIndividual, OntologyRelationship]]):
                The dependence of the order of the elements is maintained
                for the calls with `*individuals`. No `None` values
                are contained in the result (such identifiers or individuals
                are simply skipped). Moreover, the elements returned are now
                pairs of individualsand the relationship connecting this
                individual to such ones. This description corresponds to any
                call of the form `iter(..., return_rel=True)`.


        Raises:
            TypeError: Objects that are not ontology individuals,
                identifiers or strings provided as positional arguments.
            TypeError: Object that is not an ontology relationship or the
                identifier of an ontology relationship passed as keyword
                argument `rel`.
            TypeError: Object that is not an ontology class passed as
                keyword argument `oclass`.
            RuntimeError: Ontology individuals that belong to a different
                session provided.
        """
        identifiers = list(individuals)
        for n, x in enumerate(identifiers):
            if not isinstance(x, (OntologyIndividual, Identifier, str)):
                raise TypeError(
                    f"Expected {OntologyIndividual}, {Identifier} or {str} "
                    f"objects, not {type(x)}."
                )
            elif isinstance(x, OntologyIndividual) and x not in self.session:
                raise RuntimeError(
                    "Cannot get an individual that belongs to "
                    "a different session, please add it to this session "
                    "first using `session.add`."
                )

            identifiers[n] = UID(
                x.identifier if isinstance(x, OntologyIndividual) else x
            )

        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier_typed(
                rel, typing=OntologyRelationship
            )
        elif not isinstance(rel, OntologyRelationship):
            raise TypeError(
                "Found object of type %s passed to argument rel. "
                "Should be an OntologyRelationship." % type(rel)
            )

        if oclass is not None and not isinstance(oclass, OntologyClass):
            raise TypeError(
                "Found object of type %s passed to argument "
                "oclass. Should be an OntologyClass." % type(oclass)
            )

        relationship_set = RelationshipSet(
            rel, self, oclass=oclass, uids=tuple(identifiers) or None
        )

        # In the following section, return is used instead of yield so that
        # code runs until the `return` statement when iter is called (
        # otherwise the exceptions above would not be raised until the first
        # item from the iterator is requested).
        if not return_rel:
            iterator = iter(relationship_set)
        else:

            def iterator() -> Iterator[
                Tuple[OntologyIndividual, OntologyRelationship]
            ]:
                """Helper iterator.

                The purpose of defining this iterator is to be able to
                return it, instead of using the `yield` keyword on the main
                function, as described on the comment above.
                """
                for (i, r, t) in relationship_set.iter_low_level():
                    if not t:
                        continue
                    session = self.session
                    yield (
                        (
                            session.from_identifier_typed(
                                i, typing=OntologyIndividual
                            ),
                            session.ontology.from_identifier_typed(
                                r, typing=OntologyRelationship
                            ),
                        )
                    )

            iterator = iterator()
        return iterator

    @property
    def operations(self) -> OperationsNamespace:
        """Access operations specific this individual's class."""
        if self._operations_namespace is None:
            self._operations_namespace = OperationsNamespace(individual=self)
        return self._operations_namespace

    @property
    def attributes(
        self,
    ) -> Mapping[OntologyAttribute, FrozenSet[AttributeValue]]:
        """Get the attributes of this individual as a dictionary."""
        generator = self.attributes_attribute_and_value_generator()
        return MappingProxyType(
            {attr: frozenset(gen) for attr, gen in generator}
        )

    def is_subclass_of(self, ontology_class: OntologyEntity) -> bool:
        """Check if the individual is an instance of the given ontology class.

        Args:
            ontology_class: The ontology class to test against.

        Returns:
            Whether the ontology individual is an instance of such ontology
                class.
        """
        return bool(set(self.classes) & set(ontology_class.subclasses))

    # ↑ ------ ↑
    # Public API

    def __enter__(self) -> ContainerEnvironment:
        """Use an ontology individual as a context manager.

        At the moment, individuals cannot be used as a context manager,
        except for containers.

        Returns:
            A `ContainerEnvironment` object when a container is used as a
            context manager. `ContainerEnvironment` objects have the same
            functionality as the operations defined for a container,
            but those can be called directly.

        Raises:
            AttributeError: When an ontology individual which does not
                belong to the `Container` subclass is used as a context
                manager.
        """
        classes = {class_.identifier for class_ in self.superclasses}

        if simphony_namespace.Container in classes:
            # Triggers the creation of the operations instance and thus the
            # environment.
            environment = self.operations.environment
            self._operations_context = environment
            return environment.__enter__()

        raise AttributeError("__enter__")

    def __exit__(self, *args):
        """Leave the individual's context manager when used as such.

        At the moment, individuals cannot be used as a context manager,
        except for containers.

        Raises:
            AttributeError: When the method `__enter__` has not been called
                on the individual before.
        """
        if self._operations_context is not None:
            context_return = self._operations_context.__exit__(*args)
            self._operations_context = None
            return context_return

        raise AttributeError("__exit__")

    _operations_namespace: Optional[OperationsNamespace] = None
    """Holds the operations namespace instance for this ontology individual.

    The namespace in turns holds the instances of any subclasses of
    `Operation` that were defined and compatible with the classes of the
    individual.
    """

    _operations_context: Optional[ContainerEnvironment] = None
    """Stores the current context object.

    Some individuals (currently only containers) can be used as context
    managers through the operations API. The way this works is the
    following: when the `with` statement is used, an operation on the
    individual is called that retrieves the actual context manager object
    (which is not an individual) and calls the `__enter__` method from it.

    This context manager object needs to be stored somewhere so that when
    the individual context manager is exited, the actual context manager
    object's `__exit__` method is also called. This is the purpose of this
    attribute.
    """

    def _attribute_autocompletion(self) -> Iterable[str]:
        """Compute individual's attributes as autocompletion suggestions."""
        result = iter(())
        attributes = (
            attr
            for oclass in self.classes
            for attr in chain(
                oclass.attributes.keys(),
                oclass.optional_attributes,
                self.attributes_generator(),
            )
        )
        for attribute in attributes:
            result = chain(
                result,
                attribute.iter_labels(return_literal=False),
                (attribute.iri[len(attribute.namespace.iri) :],),
            )
        return result

    def _relationship_autocompletion(self) -> Iterable[str]:
        """Compute individual's relationships as autocompletion suggestions."""
        result = iter(())
        relationships = (
            relationship
            for _, relationship in self.relationships_iter(return_rel=True)
        )
        for relationship in relationships:
            result = chain(
                result,
                relationship.iter_labels(return_literal=False),
                (relationship.iri[len(relationship.namespace.iri) :],),
            )
        return result

    def _annotation_autocompletion(self) -> Iterable[str]:
        """Compute individual's annotations as autocompletion suggestions."""
        result = iter(())
        annotation_properties = (
            annotation for annotation, _ in self.annotations_iter()
        )
        for annotation in annotation_properties:
            result = chain(
                result,
                annotation.iter_labels(
                    return_literal=False, return_prop=False
                ),
                (annotation.iri[len(annotation.namespace.iri) :],),
            )
        return result

    def _get_direct_superclasses(self) -> Iterable[OntologyClass]:
        yield from (
            x for oclass in self.classes for x in oclass.direct_superclasses
        )

    def _get_direct_subclasses(self) -> Iterable[OntologyClass]:
        yield from (
            x for oclass in self.classes for x in oclass.direct_subclasses
        )

    def _get_superclasses(self) -> Iterable[OntologyClass]:
        yield from (x for oclass in self.classes for x in oclass.superclasses)

    def _get_subclasses(self) -> Iterable[OntologyClass]:
        yield from (x for oclass in self.classes for x in oclass.subclasses)

    # Annotation handling
    # ↓ --------------- ↓

    @staticmethod
    def _classify_by_type(
        values: Set[PredicateValue],
    ) -> Dict[Type[PredicateValue], PredicateValue]:
        values = {
            type_: tuple(filter(lambda x: isinstance(x, type_), values))
            for type_ in (
                OntologyAnnotation,
                OntologyAttribute,
                OntologyClass,
                OntologyIndividual,
                OntologyRelationship,
                ATTRIBUTE_VALUE_TYPES,
                URIRef,
                Literal,
            )
        }
        values = {key: value for key, value in values.items() if value}
        return values

    def annotations_add(
        self,
        annotation: OntologyAnnotation,
        values: Union[
            Dict[Type[AnnotationValue], AnnotationValue], Set[AnnotationValue]
        ],
    ) -> None:
        """Adds annotations to the ontology individual."""
        if not isinstance(values, dict):
            values = self._classify_by_type(values)
        for value in chain(
            *(
                values.get(key, set())
                for key in (
                    OntologyAnnotation,
                    OntologyAttribute,
                    OntologyClass,
                    OntologyIndividual,
                    OntologyRelationship,
                )
            )
        ):
            self.session.graph.add((self.iri, annotation.iri, value.iri))
        for value in values.get(Literal, set()):
            self.session.graph.add((self.iri, annotation.iri, value))
        for value in values.get(ATTRIBUTE_VALUE_TYPES, set()):
            self.session.graph.add((self.iri, annotation.iri, Literal(value)))
        for value in values.get(URIRef, set()):
            self.session.graph.add((self.iri, annotation.iri, value))

    def annotations_delete(
        self,
        annotation: OntologyAnnotation,
        values: Union[
            Dict[Type[AnnotationValue], Union[AnnotationValue]],
            Set[AnnotationValue],
        ],
    ) -> None:
        """Deletes an annotation from an individual."""
        if not isinstance(values, dict):
            values = self._classify_by_type(values)

        for value in values.get(Literal, set()):
            self.session.graph.remove((self.iri, annotation.iri, value))
        for value in values.get(ATTRIBUTE_VALUE_TYPES, set()):
            self.session.graph.remove(
                (self.iri, annotation.iri, Literal(value))
            )
        for value in values.get(URIRef, set()):
            self.session.graph.remove((self.iri, annotation.iri, value))

    def annotations_set(
        self,
        annotation: OntologyAnnotation,
        values: Union[
            Dict[Type[AnnotationValue], AnnotationValue], Set[AnnotationValue]
        ],
    ) -> None:
        """Replaces the annotations of an individual."""
        if not isinstance(values, dict):
            values = self._classify_by_type(values)

        self.session.graph.remove((self.iri, annotation.iri, None))
        for value in chain(
            *(
                values.get(key, set())
                for key in (
                    OntologyAnnotation,
                    OntologyAttribute,
                    OntologyClass,
                    OntologyIndividual,
                    OntologyRelationship,
                )
            )
        ):
            self.session.graph.add((self.iri, annotation.iri, value.iri))
        for value in values.get(Literal, set()):
            self.session.graph.add((self.iri, annotation.iri, value))
        for value in values.get(ATTRIBUTE_VALUE_TYPES, set()):
            self.session.graph.add((self.iri, annotation.iri, Literal(value)))
        for value in values.get(URIRef, set()):
            self.session.graph.add((self.iri, annotation.iri, value))

    def annotations_value_generator(
        self, annotation: OntologyAnnotation
    ) -> Iterator[AnnotationValue]:
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

    def annotations_iter(
        self,
        rel: Optional[Union[OntologyAnnotation, Identifier]] = None,
        return_rel: bool = False,
    ) -> Iterator[AnnotationValue]:
        """Iterate over the connected ontology individuals.

        Args:
            rel: Only return the annotation values which are connected by
                the given annotation. Defaults to None (any relationship).
            return_rel: Whether to return the connecting
                relationship. Defaults to False.

        Returns:
            Iterator with the queried ontology individuals.
        """
        if isinstance(rel, Identifier):
            rel = self.session.ontology.from_identifier_typed(
                rel, typing=OntologyAnnotation
            )
        entities_and_annotations = (
            (
                self.session.from_identifier(o),
                self.session.ontology.from_identifier(p),
            )
            for s, p, o in self.session.graph.triples(
                (self.identifier, None, None)
            )
            if not (isinstance(o, Literal) or p == RDF.type)
        )
        entities_and_annotations = filter(
            lambda x: (
                isinstance(x[1], OntologyAnnotation)
                and (x[1].is_subclass_of(rel) if rel is not None else True)
            ),
            entities_and_annotations,
        )
        if return_rel:
            yield from entities_and_annotations
        else:
            yield from map(lambda x: x[0], entities_and_annotations)

    # ↑ --------------- ↑
    # Annotation handling

    # Attribute handling
    # ↓ -------------- ↓

    def _attributes_get_by_name(self, name: str) -> Set[OntologyAttribute]:
        """Get an attribute of this individual by name."""
        attributes = (
            attr
            for oclass in self.classes
            for attr in chain(
                oclass.attributes.keys(),
                oclass.optional_attributes,
                self.attributes_generator(),
            )
        )
        attributes = (
            attr
            for attr in attributes
            if any(
                (
                    str(attr.identifier).endswith(name),
                    name in attr.iter_labels(return_literal=False),
                )
            )
        )
        return set(attributes)

    def attributes_add(
        self, attribute: OntologyAttribute, values: Iterable[AttributeValue]
    ):
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
        values = (
            attribute.convert_to_datatype(value)
            for value in values
            if value is not None
        )
        for value in values:
            self.session.graph.add(
                (
                    self.iri,
                    attribute.iri,
                    Literal(
                        value,
                        datatype=attribute.datatype,
                    ),
                )
            )

    def attributes_delete(
        self, attribute: OntologyAttribute, values: Iterable[AttributeValue]
    ):
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
        values = (
            attribute.convert_to_datatype(value)
            for value in values
            if value is not None
        )
        for value in values:
            self.session.graph.remove(
                (
                    self.iri,
                    attribute.iri,
                    Literal(
                        value,
                        datatype=attribute.datatype,
                    ),
                )
            )

    def attributes_set(
        self,
        attribute: OntologyAttribute,
        values: Iterable[Union[AttributeValue, Literal]],
    ):
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

    def attributes_value_generator(
        self, attribute: OntologyAttribute
    ) -> Iterator[AttributeValue]:
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
            literal = Literal(
                str(literal), datatype=literal.datatype, lang=literal.language
            )
            yield literal.toPython()

    def attributes_value_contains(
        self, attribute: OntologyAttribute, value: AttributeValue
    ) -> bool:
        """Whether a specific value is assigned to the specified attribute.

        Args:
            attribute: The ontology attribute query for values.

        Returns:
            Whether the specific value is assigned to the specified
            attribute or not.
        """
        if attribute.datatype in (None, RDF.langString):
            return any(
                str(value) == str(x)
                for x in self.session.graph.objects(self.iri, attribute.iri)
                if isinstance(x, Literal)
            )
        else:
            literal = Literal(value, datatype=attribute.datatype)
            literal = Literal(str(literal), datatype=attribute.datatype)
            return literal in self.session.graph.objects(
                self.iri, attribute.iri
            )

    def attributes_generator(self) -> Iterator[OntologyAttribute]:
        """Returns a generator of the attributes of this CUDS object.

        The generator only returns the OntologyAttribute objects, NOT the
        values.

        Returns:
            Generator that returns the attributes of this CUDS object.
        """
        for predicate in self.session.graph.predicates(self.iri, None):
            try:
                obj = self.session.ontology.from_identifier_typed(
                    predicate, typing=OntologyAttribute
                )
            except (KeyError, TypeError):
                continue
            if isinstance(obj, OntologyAttribute):
                yield obj

    def attributes_attribute_and_value_generator(
        self,
    ) -> Iterator[Tuple[OntologyAttribute, Iterator[AttributeValue]]]:
        """Returns a generator of both the attributes and their values.

        Returns:
            Generator that yields tuples, where the first item is the ontology
            attribute and the second a generator of values for such attribute.
        """
        for attribute in self.attributes_generator():
            yield attribute, self.attributes_value_generator(attribute)

    # ↑ -------------- ↑
    # Attribute handling

    # Relationship handling
    # ↓ ----------------- ↓

    def relationships_iter(
        self,
        rel: Optional[OntologyRelationship] = None,
        oclass: Optional[OntologyClass] = None,
        return_rel: bool = False,
    ) -> Union[
        Iterator[OntologyIndividual],
        Iterator[Tuple[OntologyIndividual, OntologyRelationship]],
    ]:
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

        def individuals_and_relationships() -> Iterator[
            OntologyIndividual, OntologyEntity
        ]:
            for s, p, o in self.session.graph.triples(
                (
                    self.identifier,
                    rel.identifier if rel is not None else None,
                    None,
                )
            ):
                if isinstance(o, Literal) or p == RDF.type:
                    continue
                prop = self.session.ontology.from_identifier(p)
                if not isinstance(prop, OntologyRelationship):
                    continue
                individual = self.session.from_identifier_typed(
                    o, typing=OntologyIndividual
                )
                yield individual, prop

        individuals_and_relationships = individuals_and_relationships()
        if oclass:
            individuals_and_relationships = (
                (entity, relationship)
                for entity, relationship in individuals_and_relationships
                if oclass == entity
            )

        if return_rel:
            yield from individuals_and_relationships
        else:
            yield from map(lambda x: x[0], individuals_and_relationships)

    # ↑ ----------------- ↑
    # Relationship handling
