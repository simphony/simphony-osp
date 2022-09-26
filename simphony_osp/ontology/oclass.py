"""A class defined in the ontology."""
from __future__ import annotations

import logging
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
    Optional,
    Set,
    Union,
)
from uuid import UUID

from rdflib import OWL, RDF, RDFS, BNode, URIRef
from rdflib.term import Identifier, Node

from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.composition import Composition
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.restriction import Restriction
from simphony_osp.utils.cache import lru_cache_timestamp
from simphony_osp.utils.datatypes import UID, AttributeValue, Triple

if TYPE_CHECKING:
    from simphony_osp.session.session import Session

logger = logging.getLogger(__name__)

# The RDFLib namespace object is not as fast as it should be, so it is
# useful to reuse some IRIs throughout the file.
# TODO: Send PR to RDFLib to fix this upstream.
RDF_type = RDF.type
RDFS_domain = RDFS.domain
RDFS_subClassOf = RDFS.subClassOf
OWL_DatatypeProperty = OWL.DatatypeProperty
OWL_Restriction = OWL.Restriction
OWL_Thing = OWL.Thing
OWL_allValuesFrom = OWL.allValuesFrom
OWL_bottomDataProperty = OWL.bottomDataProperty
OWL_cardinality = OWL.cardinality
OWL_minCardinality = OWL.minCardinality
OWL_hasValue = OWL.hasValue
OWL_onProperty = OWL.onProperty
OWL_someValuesFrom = OWL.someValuesFrom
OWL_topDataProperty = OWL.topDataProperty


class OntologyClass(OntologyEntity):
    """A class defined in the ontology."""

    rdf_type = {OWL.Class, RDFS.Class}
    rdf_identifier = URIRef

    # ↓ --------------------- Public API --------------------- ↓ #

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def attributes(
        self,
    ) -> Mapping[OntologyAttribute, FrozenSet[Optional[AttributeValue]]]:
        """Get the attributes of this class.

        The attributes that all instances of this class are expected to
        have. A class can have attributes because one of its superclasses
        (including itself) has a default value for an attribute, or because
        the axioms affecting the superclass explicitly state that the class has
        such an attribute.
        """
        attributes: Dict[
            OntologyAttribute, FrozenSet[Optional[AttributeValue]]
        ]
        superclass: OntologyClass

        attributes = self._direct_attributes

        # Inherit attributes from the direct superclasses, which recursively
        # inherit from their own superclasses.
        for superclass in self.direct_superclasses:
            for attribute, default in superclass.attributes.items():
                attributes[attribute] = (
                    attributes.get(attribute, None) or default
                )
        return MappingProxyType(attributes)

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def optional_attributes(self) -> FrozenSet[OntologyAttribute]:
        """Get the optional attributes of this class.

        The optional attributes are the non-mandatory attributes (those not
        returned by the `attributes` property) that have the class defined
        as their domain, or any of its superclasses.
        """
        superclass: OntologyClass
        attributes = frozenset(
            self._direct_optional_attributes
            | {
                attribute
                for superclass in self.direct_superclasses
                for attribute in superclass.optional_attributes
            }
        )
        return attributes

    @property
    def axioms(self) -> FrozenSet[Union[Restriction, Composition]]:
        """Get all the axioms for the ontology class.

        Axioms are OWL Restrictions and Compositions. Includes axioms inherited
        from its superclasses.

        Returns:
            Axioms for the ontology class.
        """
        axioms: Set[Restriction] = set()
        for superclass in self.superclasses:
            axioms |= self._compute_axioms(
                superclass.identifier, RDFS.subClassOf
            )
            axioms |= self._compute_axioms(
                superclass.identifier, OWL.equivalentClass
            )
        return frozenset(axioms)

    def __call__(
        self,
        session=None,
        iri: Optional[Union[URIRef, str]] = None,
        identifier: Optional[Union[UUID, str, Node, int, bytes]] = None,
        _force: bool = False,
        **kwargs,
    ):
        """Create an OntologyIndividual object from this ontology class.

        Args:
            identifier: The identifier of the ontology individual. When set to
                a string, has the same effect as the keyword argument `iri`.
                When set to`None`, a new identifier with a random UUID is
                generated. When set to any of the other accepted types, the
                given value is used to generate the UUID of the identifier.
                Defaults to None.
            iri: The same as the identifier, but exclusively for IRI
                identifiers.
            session: The session that the ontology individual will be stored
                in. Defaults to `None` (the default session).

        Raises:
            TypeError: Error occurred during instantiation.

        Returns:
            The new ontology individual.
        """
        if None not in (identifier, iri):
            raise ValueError(
                "Tried to initialize an ontology individual, both its IRI and "
                "UID. An ontology individual is constrained to have just one "
                "UID."
            )
        elif identifier is not None and not isinstance(
            identifier, (UID, UUID, str, Node, int, bytes)
        ):
            raise ValueError(
                "Provide an object of one of the following types as UID: "
                + ",".join(str(x) for x in (UID, UUID, str, Node, int, bytes))
            )
        elif iri is not None and not isinstance(iri, (URIRef, str, UID)):
            raise ValueError(
                "Provide an object of one of the following types as IRI: "
                + ",".join(str(x) for x in (URIRef, str, UID))
            )
        else:
            identifier = (
                (UID(identifier) if identifier else None)
                or (UID(iri) if iri else None)
                or UID()
            )

        from simphony_osp.ontology.individual import OntologyIndividual

        # build attributes dictionary by combining
        # kwargs and defaults
        return OntologyIndividual(
            uid=identifier,
            session=session,
            class_=self,
            attributes=self._kwargs_to_attributes(kwargs, _skip_checks=_force),
        )

    # ↑ --------------------- Public API --------------------- ↑ #

    def __init__(
        self,
        uid: UID,
        session: Optional[Session] = None,
        triples: Optional[Iterable[Triple]] = None,
        merge: bool = False,
    ) -> None:
        """Initialize the ontology class.

        Args:
            uid: UID identifying the ontology class.
            session: Session where the entity is stored.
            triples: Construct the class with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
        """
        super().__init__(uid, session, triples, merge=merge)

    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def _compute_axioms(
        self, identifier: Identifier, predicate: URIRef
    ) -> FrozenSet[Restriction]:
        """Compute the axioms for the class with the given identifier.

        Does not include superclasses.

        Args:
            identifier: The IRI of the class.
            predicate: The predicate to which the class is connected to
                axioms (subclass or equivalentClass).

        Returns:
            Tuple of computed axioms.
        """
        axioms: Set[Union[Restriction, Composition]] = set()
        for o in self.session.graph.objects(identifier, predicate):
            if not isinstance(o, BNode):
                continue
            if (o, RDF_type, OWL_Restriction) in self.session.graph:
                axioms.add(self.session.from_identifier_typed(o, Restriction))
            elif (o, RDF_type, OWL.Class) in self.session.graph:
                axioms.add(self.session.from_identifier_typed(o, Composition))
        return frozenset(axioms)

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def _direct_attributes(
        self,
    ) -> Dict[OntologyAttribute, FrozenSet[Optional[AttributeValue]]]:
        """Get the non-inherited attributes of this ontology class.

        Returns:
            Mapping from attributes to the default value of the attribute.
            Mandatory attributes without a default value are mapped to `None`.
        """
        graph = self.session.graph
        attributes = dict()

        # From axioms.
        restrictions_on_data_properties = (
            # Yield both the restriction and the property.
            (restriction_iri, prop_iri)
            # Must be a restriction.
            for restriction_iri in graph.objects(
                self.identifier, RDFS_subClassOf
            )
            if (restriction_iri, RDF_type, OWL_Restriction) in graph
            # The property must be a DatatypeProperty.
            for prop_iri in (
                graph.value(restriction_iri, OWL_onProperty, any=False),
            )
            if (prop_iri, RDF_type, OWL_DatatypeProperty) in graph
        )
        for restriction_iri, prop_iri in restrictions_on_data_properties:
            attribute = self.session.from_identifier_typed(
                prop_iri, typing=OntologyAttribute
            )

            # Get restriction default.
            default = graph.value(restriction_iri, OWL_hasValue)

            # Determine if attribute is mandatory.
            obligatory = any(
                (
                    self.session.graph.value(
                        restriction_iri, OWL_someValuesFrom
                    ),
                    self.session.graph.value(restriction_iri, OWL_hasValue),
                    self.session.graph.value(restriction_iri, OWL_cardinality)
                    != 0,
                    self.session.graph.value(
                        restriction_iri, OWL_minCardinality != 0
                    ),
                )
            )

            if default or obligatory:
                attributes[attribute] = attributes.get(attribute, default)

        # TODO more cases
        return attributes

    @property
    @lru_cache_timestamp(lambda self: self.session.entity_cache_timestamp)
    def _direct_optional_attributes(
        self,
    ) -> FrozenSet[OntologyAttribute]:
        """Get the non-inherited optional attributes of this ontology class.

        The optional non-inherited attributes are the non-mandatory attributes
        (those not returned by the `_direct_attributes` property) that have
        the class defined as their domain, or any of its superclasses.

        Returns:
            A frozen set containing all the non-inherited optional
            attributes of the class.
        """
        graph = self.session.graph
        attributes = set()

        # Class is part of the domain of a DatatypeProperty.
        blacklist = [OWL_topDataProperty, OWL_bottomDataProperty]
        target_properties = (
            s
            for s in graph.subjects(RDFS_domain, self.identifier)
            if (s, RDF_type, OWL_DatatypeProperty) in graph or s in blacklist
        )
        for identifier in target_properties:
            attribute = self.session.from_identifier_typed(
                identifier, typing=OntologyAttribute
            )
            attributes.add(attribute)
        return frozenset(attributes)

    def _get_direct_superclasses(self) -> Iterator[OntologyClass]:
        """Get all the direct superclasses of this ontology class.

        Returns:
            The direct superclasses.
        """
        for o in self.session.graph.objects(self.iri, RDFS_subClassOf):
            try:
                yield self.session.from_identifier_typed(
                    o, typing=OntologyClass
                )
            except TypeError:
                pass

    def _get_direct_subclasses(self) -> Iterator[OntologyClass]:
        """Get all the direct subclasses of this ontology class.

        Returns:
            The direct subclasses.
        """
        for s in self.session.graph.subjects(RDFS_subClassOf, self.iri):
            try:
                yield self.session.from_identifier_typed(
                    s, typing=OntologyClass
                )
            except TypeError:
                pass

    def _get_superclasses(self) -> Iterator[OntologyClass]:
        """Get all the superclasses of this ontology class.

        Yields:
            The superclasses.
        """
        yield self

        def closure(node, graph):
            yield from graph.objects(node, RDFS_subClassOf)

        yield from filter(
            lambda x: isinstance(x, OntologyClass),
            (
                self.session.from_identifier(x)
                for x in self.session.graph.transitiveClosure(
                    closure, self.identifier
                )
            ),
        )

        yield self.session.from_identifier(OWL_Thing)

    def _get_subclasses(self) -> Iterator[OntologyClass]:
        """Get all the subclasses of this ontology class.

        Yields:
            The subclasses.
        """
        yield self

        if self.identifier == OWL_Thing:
            for s in self.session.graph.subjects(RDF.type, OWL.Class):
                try:
                    yield self.session.from_identifier_typed(
                        s, typing=OntologyClass
                    )
                except TypeError:
                    pass
            # The filter makes sure that `Restriction` and `Composition`
            # objects are not returned.
        else:

            def closure(node, graph):
                yield from graph.subjects(RDFS_subClassOf, node)

            yield from filter(
                lambda x: isinstance(x, OntologyClass),
                (
                    self.session.from_identifier(x)
                    for x in self.session.graph.transitiveClosure(
                        closure, self.identifier
                    )
                ),
            )

    def _kwargs_to_attributes(
        self, kwargs: Mapping, _skip_checks: bool
    ) -> Mapping[OntologyAttribute, FrozenSet[Any]]:
        """Combine class attributes with the ones from the given kwargs.

        Args:
            kwargs: The user specified keyword arguments.
            _skip_checks: When true, allow mandatory attributes to be left
                undefined.

        Raises:
            TypeError: Unexpected keyword argument.
            TypeError: Missing keyword argument.

        Returns:
            The resulting mixture.
        """
        kwargs = dict(kwargs)

        attributes = dict()
        attribute_declaration = {
            attribute: (default, mandatory)
            for attribute, default, mandatory in chain(
                ((attr, None, False) for attr in self.optional_attributes),
                ((attr, def_, True) for attr, def_ in self.attributes.items()),
            )
        }
        for attribute, (
            default,
            obligatory,
        ) in attribute_declaration.items():
            labels = set(attribute.iter_labels(return_literal=False))
            if attribute.namespace is not None:
                labels |= {
                    attribute.identifier[len(attribute.namespace.iri) :]
                }
            label = next(filter(lambda x: x in kwargs, labels), None)
            if label is not None:
                attributes[attribute] = kwargs[label]
                del kwargs[label]
            elif not _skip_checks and obligatory:
                raise TypeError(
                    "Missing keyword argument: %s" % attribute.label
                )
            elif default is not None:
                attributes[attribute] = default
            else:
                continue

            # Turn attribute into a mutable sequence.
            if not isinstance(attributes[attribute], FrozenSet):
                attributes[attribute] = [attributes[attribute]]
            else:
                attributes[attribute] = list(attributes[attribute])

            # Set the appropriate hashable data type for the arguments.
            attributes[attribute] = frozenset(
                {
                    attribute.convert_to_datatype(value)
                    for value in attributes[attribute]
                }
            )

        # Check validity of arguments
        if not _skip_checks and kwargs:
            raise TypeError("Unexpected keyword arguments: %s" % kwargs.keys())
        return MappingProxyType(attributes)
