"""An ontology individual."""

import itertools
import logging
from abc import ABC, abstractmethod
from typing import (Any, Dict, Iterable, Iterator, List, MutableSet, Optional,
                    Set, TYPE_CHECKING, Tuple, Type, Union)

from rdflib import RDF, Literal, URIRef
from rdflib.term import Identifier

from osp.core.ontology.annotation import OntologyAnnotation
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.utils import DataStructureSet
from osp.core.utils.datatypes import (
    UID, RDFCompatibleType, RDF_COMPATIBLE_TYPES, Triple)

if TYPE_CHECKING:
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class OntologyIndividual(OntologyEntity):
    """An ontology individual."""

    rdf_identifier = Identifier

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
                    value: Optional[
                        Union[RDFCompatibleType,
                              Set[RDFCompatibleType]]
                    ]) -> None:
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
            value = value if value is not None else set()
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
                    value: Union['OntologyAttribute',
                                 'OntologyRelationship',
                                 Tuple[
                                     Union['OntologyAttribute',
                                           'OntologyRelationship'],
                                     slice]]) \
            -> Optional[
                Union['OntologyIndividual._AttributeSet',
                      'OntologyIndividual._RelationshipSet',
                      'OntologyIndividual',
                      RDFCompatibleType]]:
    def __getitem__(
            self,
            value: Union[OntologyAttribute, OntologyRelationship,
                         OntologyAnnotation,
                         Tuple[Union[OntologyAttribute, OntologyRelationship,
                                     OntologyAnnotation],
                               slice,
                               ]
                         ]
    ) -> Optional[Union[
        OntologyAnnotation,                     # Annotation Properties
        OntologyAttribute,                      # Annotation Properties
        'OntologyClass',                        # Annotation Properties
        'OntologyIndividual',                   # Object Properties,
                                                # Annotation Properties
        OntologyRelationship,                   # Annotation Properties
        RDFCompatibleType,                      # Datatype Properties,
                                                # Annotation Properties
        'OntologyIndividual._AttributeSet',     # Datatype Properties
        'OntologyIndividual._RelationshipSet',  # Object Properties
        'OntologyIndividual._AnnotationSet',    # Annotation Properties
        URIRef,                                 # Annotation Properties
    ]]:
        """Retrieve linked ontology individuals or attribute values.

        The subscripting syntax `individual[rel]` allows:
        - When `rel` is an OntologyRelationship, to obtain ONLY ONE
          (non-deterministic) ontology individual of all the ontology
          individuals linked to `individual` through the `rel` relationship.
        - When `rel` is an OntologyAttribute, to obtain ONLY ONE
          (non-deterministic) value of such attribute.
        - When `rel` is an OntologyAnnotation, to obtain ONLY ONE
          (non-deterministic) annotation value from all the annotation values
          linked to `individual` through the `rel` annotation property.

        The subscripting syntax `individual[rel, :]` allows:
        - When `rel` is an OntologyRelationship, to obtain a set containing
          all ontology individuals objects that are connected to `individual`
          through rel. Such set can be modified in-place to modify the
          existing connections.
        - When `rel` is an OntologyAttribute, to obtain a set containing all
          the values assigned to the specified attribute. Such set can be
          modified in-place to change the assigned values.
        - When `rel` is an OntologyAnnotation, to obtain a set containing
          all the annotation values assigned to the specified annotation
          property. Such set can be modified in-place to modify the existing
          connections.

        The reason why a set is returned and not a list, or any other
        container allowing repeated elements, is that the underlying RDF
        graph does not accept duplicate statements.

        Args:
            value: Two possibilities,
                - Just an ontology relationship, an ontology attribute,
                  or an ontology annotation (OWL datatype property,
                  OWL object property, OWL annotation property). Then only one
                  ontology individual, attribute value or annotation value is
                  returned.
                - A tuple (multiple keys specified). The first element of the
                  tuple is expected to be such attribute, relationship,
                  or annotation property, and the second a `slice` object.
                  When `slice(None, None, None)` (equivalent to `:`) is
                  provided, a set-like object of values is returned.
                  This is the the only kind of slice supported.

        Raises:
            TypeError: Trying to use something that is neither an
                OntologyAttribute, an OntologyRelationship or an
                OntologyAnnotation as index.
            IndexError: When invalid slicing is provided.
        """
        # Translate input between brackets to slicing syntax.
        if isinstance(value, tuple):
            rel, slicing = value
        else:
            rel, slicing = value, None

        # Select the appropriate set to handle the query.
        if isinstance(rel, OntologyAttribute):
            set_class = self._AttributeSet
        elif isinstance(rel, OntologyRelationship):
            set_class = self._RelationshipSet
        elif isinstance(rel, OntologyAnnotation):
            set_class = self._AnnotationSet
        else:
            raise TypeError(f'Ontology individual indices must be ontology '
                            f'relationships, ontology attributes, '
                            f'or ontology annotations, not {type(rel)}.')

        # Return the result of the query.
        if slicing is None:
            try:
                return set(set_class(rel, self)).pop()
            except KeyError:
                return None
        elif slicing == slice(None, None, None):
            return set_class(rel, self)
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

    def __setitem__(
            self,
            rel: Union[OntologyAttribute, OntologyRelationship,
                       OntologyAnnotation],
            values: Optional[Union[
                Union[OntologyAnnotation,    # Annotation Properties
                      OntologyAttribute,     # Annotation Properties
                      'OntologyClass',       # Annotation Properties
                      'OntologyIndividual',  # Object Properties,
                                             # Annotation Properties
                      OntologyRelationship,  # Annotation Properties
                      RDFCompatibleType,     # Datatype Properties,
                                             # Annotation Properties
                      URIRef,                # Annotation Properties
                      Literal,               # Annotation Properties
                      ],
                Set[Union[
                    OntologyAnnotation,      # Annotation Properties
                    OntologyAttribute,       # Annotation Properties
                    OntologyClass,           # Annotation Properties
                    'OntologyIndividual',    # Object Properties,
                                             # Annotation Properties
                    OntologyRelationship,    # Annotation Properties
                    RDFCompatibleType,       # Datatype Properties,
                                             # Annotation Properties
                    URIRef,                  # Annotation Properties
                    Literal,                 # Annotation Properties
                ]],
            ]]
    ) -> None:
        """Manages both individuals object properties and data properties.

        The subscripting syntax `individual[rel] = ` allows,

        - When `rel` is an OntologyRelationship, to replace the list of
          ontology individuals that are connected to `individual` through rel.
        - When `rel` is an OntologyAttribute, to replace the values of
          such attribute.
        - When `rel` is an OntologyAnnotation, to replace the annotation
          values of such annotation property.

        The subscripting syntax `individual[rel, :] = `, even though not
        considered on the type hints is also accepted. However, but the effect
        it produces is the same. It is nevertheless required with in-place
        operators such as `+=` or `&=` if one wants to operate on the set of
        attributes values rather than on the attribute. See the docstring of
        `__getitem__` for more details.

        This function only accepts hashable objects as input, as the
        underlying RDF graph does not accept duplicate statements.

        Args:
            rel: Either an ontology attribute, an ontology relationship or
                an ontology annotation (OWL datatype property, OWL object
                property).
            values: Either a single element compatible with the OWL standard
                (this includes ontology individuals objects) or a set of such
                elements.

        Raises:
            TypeError: Trying to assign attributes using an object property,
                trying to assign ontology individuals using a data property,
                trying to use something that is neither an OntologyAttribute
                or an OntologyRelationship as index.
        """
        # Get relationship from input between brackets. Slices are ignored.
        if isinstance(rel, tuple) and rel[1] == slice(None, None, None):
            rel = rel[0]

        # Put values in set form.
        values = values if values is not None else set()
        # Apparently instances of MutableSet are not instances of Set.
        values = {values} \
            if not isinstance(values, (Set, MutableSet)) \
            else values

        # Classify the values.
        values = self._classify_annotation_values(values)

        # Prevent illegal assignments.
        if isinstance(rel, OntologyRelationship):
            if ((len(values) > 0 and OntologyIndividual not in values)
                    or len(values) > 1):
                raise TypeError(f'Trying to assign python objects which are '
                                f'not ontology individuals using an object '
                                f'property {rel}.')
        elif isinstance(rel, OntologyAttribute):
            if ((len(values) > 0
                 and all(x not in values
                         for x in (RDF_COMPATIBLE_TYPES, Literal)))
                    or len(values) > 2):
                raise TypeError(f'Trying to assign python objects which '
                                f'cannot be interpreted as literals '
                                f'using a data property {rel}.')
        elif isinstance(rel, OntologyAnnotation):
            pass
        else:
            raise TypeError(f'Expected one of %s, not {type(rel)}.'
                            % ', '.join(map(str,
                                            [OntologyAnnotation,
                                             OntologyAttribute,
                                             OntologyRelationship]))
                            )

        # Perform assignments.
        if isinstance(rel, OntologyRelationship):
            individuals_set = set(values.get(OntologyIndividual, set()))
            existing_set = set(self._iter(rel=rel))
            to_connect = individuals_set - existing_set
            for individual in to_connect:
                self._connect(individual, rel=rel)
            to_disconnect = existing_set - individuals_set
            for individual in to_disconnect:
                self._disconnect(individual, rel=rel)
        elif isinstance(rel, OntologyAttribute):
            self._set_attributes(rel,
                                 set(values.get(RDF_COMPATIBLE_TYPES, set()))
                                 | set(values.get(Literal, set())))
        elif isinstance(rel, OntologyAnnotation):
            self._set_annotations(rel, values)
        else:
            raise TypeError(f'Ontology individual indices must be ontology '
                            f'relationships, ontology attributes or ontology '
                            f'annotations not {type(rel)}.')

    def __delitem__(self, rel: Union[OntologyAnnotation,
                                     OntologyAttribute,
                                     OntologyRelationship]):
        """Delete all objects attached through rel.

        Args:
            rel: Either an ontology attribute, an ontology relationship or
                an ontology annotation (OWL datatype property, OWL object
                property, OWL annotation property).
        """
        self.__setitem__(rel=rel, values=set())

    # ↑ ------ ↑
    # Public API

    class _ObjectSet(DataStructureSet):
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
        _predicate: Union[OntologyAttribute, OntologyRelationship,
                          OntologyAnnotation]
        _individual: "OntologyIndividual"

        def __init__(self,
                     predicate: Union[OntologyAttribute,
                                      OntologyRelationship,
                                      OntologyAnnotation],
                     individual: "OntologyIndividual"):
            """Fix the linked property and CUDS object."""
            self._individual = individual
            self._predicate = predicate
            super().__init__()

        def __repr__(self) -> str:
            """Return repr(self)."""
            return super().__repr__() \
                + f' <({self._predicate.__repr__()}) of ontology individual ' \
                  f'{self._individual}>'

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
                 rel: OntologyRelationship) -> "OntologyIndividual":
        """Connect an ontology individual to this one.

        If the connected object is associated with the same session, only a
        link is created. Otherwise, the information associated with the
        connected object is added to the session of this ontology individual.

        Args:
            other: The ontology individual to connect.
            rel: The relationship to use.

        Raises:
            TypeError: No relationship given.

        Returns:
            The ontology individual that has been connected,
            associated with the session of the current ontology individual
            object.
        """
        self.session.merge(other)
        self.session.graph.add(
            (self.identifier, rel.identifier, other.identifier))
        return self.session.from_identifier(other.identifier)

    def _disconnect(self,
                    other: Optional["OntologyIndividual"] = None,
                    rel: Optional[OntologyRelationship] = None):
        """Disconnect ontology individuals from this one.

        Args:
            other: The ontology individual to disconnect. When not
                specified, this ontology individual will be disconnected
                from all connected individuals
            rel: This ontology individual will be disconnected from `other`
                for relationship `rel`. When not specified, this ontology
                individual will be disconnected from `other` for all
                relationships.
        """
        self.session.graph.remove(
            (self.identifier,
             rel.identifier if rel is not None else None,
             other.identifier if other is not None else None))

    def _iter(self,
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

    class _RelationshipSet(_ObjectSet):
        """A set interface to an ontology individual's relationships.

        This class looks like and acts like the standard `set`, but it
        is an interface to the `_connect`, `_disconnect` and `_iter` methods.

        When an instance is read, the method `_iter` is used to fetch the
        data. When it is modified in-place, the methods `_connect` and
        `_disconnect` are used to reflect the changes.

        This class does not hold any relationship-related information itself,
        thus it is safe to spawn multiple instances linked to the same
        relationship and ontology individual (when single-threading).
        """
        _predicate: OntologyRelationship
        _individual: "OntologyIndividual"

        def __init__(self,
                     relationship: OntologyRelationship,
                     individual: 'OntologyIndividual'):
            """Fix the liked OntologyRelationship and ontology individual."""
            super().__init__(relationship, individual)

        @property
        def _underlying_set(self) -> Set["OntologyIndividual"]:
            """The individuals assigned to relationship`self._predicate`.

            Returns:
                The mentioned underlying set.
            """
            return set(self._individual._iter(rel=self._predicate))

        def update(self, other: Iterable['OntologyIndividual']) -> None:
            """Update the set with the union itself and other."""
            for individual in other:
                self._individual._connect(individual, rel=self._predicate)

        def intersection_update(self, other: Iterable['OntologyIndividual'])\
                -> None:
            """Update the set with the intersection of itself and another."""
            underlying_set = self._underlying_set
            intersection = underlying_set.intersection(other)
            removed = underlying_set.difference(intersection)
            for individual in removed:
                self._individual._disconnect(individual, rel=self._predicate)

        def difference_update(self, other: Iterable['OntologyIndividual']) \
                -> None:
            """Remove all elements of another set from this set."""
            to_remove = self._underlying_set & set(other)
            for individual in to_remove:
                self._individual._disconnect(individual, rel=self._predicate)

        def symmetric_difference_update(self,
                                        other: Iterable['OntologyIndividual'])\
                -> None:
            """Update with the symmetric difference of it and another."""
            result = self._underlying_set ^ set(other)
            to_add = result.difference(self._underlying_set)
            to_remove = self._underlying_set.difference(result)
            for individual in to_remove:
                self._individual._disconnect(individual, rel=self._predicate)
            for individual in to_add:
                self._individual._connect(individual, rel=self._predicate)

    # ↑ ----------------- ↑
    # Relationship handling

    # Annotation handling
    # ↓ --------------- ↓

    class _AnnotationSet(_ObjectSet, MutableSet):
        _predicate: OntologyAnnotation
        _individual: "OntologyIndividual"

        @property
        def _underlying_set(self) -> Set[Union[
            OntologyAnnotation,
            OntologyAttribute,
            OntologyClass,
            'OntologyIndividual',
            OntologyRelationship,
            RDFCompatibleType,
            URIRef,
        ]]:
            """The set of values assigned to the linked annotation.

            Returns:
                The mentioned underlying set.
            """
            return set(
                self._individual._annotation_value_generator(
                    annotation=self._predicate
                ))

        def __init__(self,
                     annotation: OntologyAnnotation,
                     individual: "OntologyIndividual") -> None:
            """Fix the linked OntologyAnnotation and ontology individual."""
            super().__init__(annotation, individual)

        def __len__(self):
            """Return len(self)."""
            return sum(
                1 for _ in self._individual._annotation_value_generator(
                    annotation=self._predicate))

        def __ior__(self,
                    other: Set[Union[
                        OntologyAnnotation,
                        OntologyAttribute,
                        OntologyClass,
                        'OntologyIndividual',
                        OntologyRelationship,
                        RDFCompatibleType,
                        URIRef,
                    ]]) -> 'OntologyIndividual._AnnotationSet':
            """Return self|=other."""
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self | other)
            return self

        def __iand__(self,
                     other: Set[Union[
                         OntologyAnnotation,
                         OntologyAttribute,
                         OntologyClass,
                         'OntologyIndividual',
                         OntologyRelationship,
                         RDFCompatibleType,
                         URIRef,
                     ]]) -> 'OntologyIndividual._AnnotationSet':
            """Return self&=other."""
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self & other)
            return self

        def __ixor__(self,
                     other: Set[Union[
                         OntologyAnnotation,
                         OntologyAttribute,
                         OntologyClass,
                         'OntologyIndividual',
                         OntologyRelationship,
                         RDFCompatibleType,
                         URIRef,
                     ]]) -> 'OntologyIndividual._AnnotationSet':
            """Return self^=other."""
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self ^ other)
            return self

        def __isub__(self,
                     other: Any) -> 'OntologyIndividual._AnnotationSet':
            """Return self-=other."""
            if isinstance(other, (Set, MutableSet)):
                # Apparently instances of MutableSet are not instances of Set.
                self._individual._set_annotations(annotation=self._predicate,
                                                  values=self - other)
            else:
                self._individual._set_annotations(annotation=self._predicate,
                                                  values=self - {other})
            return self

        def clear(self) -> None:
            """Remove all elements from this set.

            This also removed all the values assigned to the annotation
            linked to this set for the individual linked to this set.
            """
            self._individual._set_annotations(annotation=self._predicate,
                                              values=set())

        def pop(self) -> Union[
            OntologyAnnotation,
            OntologyAttribute,
            OntologyClass,
            'OntologyIndividual',
            OntologyRelationship,
            RDFCompatibleType,
            URIRef,
        ]:
            """Remove and return an arbitrary set element.

            Raises KeyError if the set is empty.
            """
            result = self._underlying_set.pop()
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self - {result})
            return result

        def difference_update(self, other: Iterable):
            """Remove all elements of another set from this set."""
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self - set(other))

        def discard(self, other: Any):
            """Remove an element from a set if it is a member.

            If the element is not a member, do nothing.
            """
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self - {other})

        def intersection(self, other: set) -> Set[Union[
            OntologyAnnotation,
            OntologyAttribute,
            OntologyClass,
            'OntologyIndividual',
            OntologyRelationship,
            RDFCompatibleType,
            URIRef,
        ]]:
            """Return the intersection of two sets as a new set.

            (i.e. all elements that are in both sets.)
            """
            return super().intersection(other)

        def remove(self, other: Any):
            """Remove an element from a set; it must be a member.

            If the element is not a member, raise a KeyError.
            """
            if other in self._underlying_set:
                self._individual._set_annotations(annotation=self._predicate,
                                                  values=self - {other})
            else:
                raise KeyError(f"{other}")

        def update(self, other: Iterable):
            """Update a set with the union of itself and others."""
            self._individual._set_annotations(annotation=self._predicate,
                                              values=self | set(other))

    @staticmethod
    def _classify_annotation_values(
            values: Set[Union[
                OntologyAnnotation,      # Annotation Properties
                OntologyAttribute,       # Annotation Properties
                OntologyClass,           # Annotation Properties
                'OntologyIndividual',    # Object Properties,
                                         # Annotation Properties
                OntologyRelationship,    # Annotation Properties
                RDFCompatibleType,       # Datatype Properties,
                                         # Annotation Properties
                URIRef,                  # Annotation Properties
                Literal,                 # Annotation Properties
            ]]
    ):
        values = {type_: tuple(filter(lambda x: isinstance(x, type_), values))
                  for type_ in (OntologyAnnotation, OntologyAttribute,
                                OntologyClass, OntologyIndividual,
                                OntologyRelationship, RDF_COMPATIBLE_TYPES,
                                URIRef, Literal)}
        values = {key: value
                  for key, value in values.items()
                  if value}
        return values

    def _set_annotations(self,
                         annotation: OntologyAnnotation,
                         values: Union[
                             Dict[
                                 Union[
                                     Type[OntologyAnnotation],
                                     Type[OntologyAttribute],
                                     Type[OntologyClass],
                                     Type['OntologyIndividual'],
                                     Type[OntologyRelationship],
                                     Type[Literal],
                                     Type[RDFCompatibleType],
                                     Type[URIRef],
                                 ],
                                 Union[
                                     Iterable[OntologyAnnotation],
                                     Iterable[OntologyAttribute],
                                     Iterable[OntologyClass],
                                     Iterable['OntologyIndividual'],
                                     Iterable[OntologyRelationship],
                                     Iterable[Literal],
                                     Iterable[RDFCompatibleType],
                                     Iterable[URIRef]
                                 ],
                             ],
                             Set[Union[
                                 OntologyAnnotation,
                                 OntologyAttribute,
                                 OntologyClass,
                                 'OntologyIndividual',
                                 OntologyRelationship,
                                 RDFCompatibleType,
                                 URIRef,
                                 Literal,
                             ]]
                         ]) -> None:
        if not isinstance(values, dict):
            values = self._classify_annotation_values(values)

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
        for value in values.get(RDF_COMPATIBLE_TYPES, set()):
            self.session.graph.add(
                (self.iri, annotation.iri,
                 Literal(value))
            )
        for value in values.get(URIRef, set()):
            self.session.graph.add((self.iri, annotation.iri, value))

    def _annotation_value_generator(self,
                                    annotation: OntologyAnnotation) \
            -> Iterator[Union[
                OntologyAnnotation,
                OntologyAttribute,
                OntologyClass,
                'OntologyIndividual',
                OntologyRelationship,
                RDFCompatibleType,
                URIRef
            ]]:
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

    def get_attributes(self) -> Dict[OntologyAttribute,
                                     Set[RDFCompatibleType]]:
        """Get the attributes of this individual as a dictionary."""
        return {attribute: set(value_generator)
                for attribute, value_generator
                in self._attribute_and_value_generator()}

    def _get_ontology_attribute_by_name(self, name: str) -> OntologyAttribute:
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

        for value in filter(lambda v: v is not None, values):
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
                        values: Iterable[Union[RDFCompatibleType,
                                               Literal]]):
        """Replace values assigned to a datatype property.

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
            if not isinstance(x, (RDF_COMPATIBLE_TYPES, Literal)):
                logger.warning(f"Type '{type(x)}' of object {x} cannot "
                               f"be set as attribute value, as it is "
                               f"incompatible with the OWL standard")

        self.session.graph.remove((self.iri, attribute.iri, None))
        self._add_attributes(attribute, values)

    def _attribute_value_generator(self,
                                   attribute: OntologyAttribute) \
            -> Iterator[RDFCompatibleType]:
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

    def _attribute_generator(self) \
            -> Iterator[OntologyAttribute]:
        """Returns a generator of the attributes of this CUDS object.

        The generator only returns the OntologyAttribute objects, NOT the
        values.

        Returns:
            Generator that returns the attributes of this CUDS object.
        """
        for predicate in self.session.graph.predicates(self.iri, None):
            try:
                obj = self.session.from_identifier(predicate)
            except KeyError:
                obj = None
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

        def __init__(self,
                     attribute: OntologyAttribute,
                     individual: "OntologyIndividual"):
            """Fix the liked OntologyAttribute and ontology individual."""
            super().__init__(attribute, individual)

        @property
        def _underlying_set(self) -> Set[RDFCompatibleType]:
            """The set of values assigned to the attribute `self._predicate`.

            Returns:
                The mentioned underlying set.
            """
            return set(
                self._individual._attribute_value_generator(
                    attribute=self._predicate))

        def update(self, other: Iterable[RDFCompatibleType]) -> None:
            """Update the set with the union of itself and others."""
            self._individual._add_attributes(self._predicate, other)

        def intersection_update(self, other: Iterable[RDFCompatibleType]) ->\
                None:
            """Update the set with the intersection of itself and another."""
            underlying_set = self._underlying_set
            intersection = underlying_set.intersection(other)
            removed = underlying_set.difference(intersection)
            self._individual._delete_attributes(self._predicate, removed)

        def difference_update(self, other: Iterable[RDFCompatibleType]) -> \
                None:
            """Remove all elements of another set from this set."""
            self._individual._delete_attributes(self._predicate,
                                                self._underlying_set
                                                & set(other))

        def symmetric_difference_update(self, other: Set[RDFCompatibleType])\
                -> None:
            """Update set with the symmetric difference of it and another."""
            self._individual._set_attributes(self._predicate,
                                             self._underlying_set ^ set(other))

    # ↑ -------------- ↑
    # Attribute handling

    def __init__(self,
                 uid: Optional[UID] = None,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False,
                 class_: Optional[OntologyClass] = None,
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
