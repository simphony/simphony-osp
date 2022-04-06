"""Restrictions on on ontology classes."""

import logging
from enum import Enum

import rdflib
from rdflib.term import BNode

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.relationship import OntologyRelationship

logger = logging.getLogger(__name__)


class QUANTIFIER(Enum):
    """The different quantifiers for restrictions."""

    SOME = 1
    ONLY = 2
    EXACTLY = 3
    MIN = 4
    MAX = 5
    VALUE = 6


class RTYPE(Enum):
    """The two types of restrictions."""

    ATTRIBUTE_RESTRICTION = 1
    RELATIONSHIP_RESTRICTION = 2


class Restriction:
    """A class to represet restrictions on ontology classes."""

    def __init__(self, bnode, namespace_registry):
        """Initialize the restriction class.

        Args:
            bnode (BNode): The blank node that represents the restriction.
            namespace_registry (NamespaceRegistry): The global namespace
                registry that contains all the OSP-core namespaces.
        """
        self._bnode = bnode
        self._graph = namespace_registry._graph
        self._namespace_registry = namespace_registry
        self._cached_quantifier = None
        self._cached_property = None
        self._cached_target = None
        self._cached_type = None

    def __str__(self):
        """Transform to string."""
        return " ".join(
            map(str, (self._property, self.quantifier, self.target))
        )

    @property
    def quantifier(self):
        """Get the quantifier of the restriction.

        Returns:
            QUANTIFIER: The quantifier of the restriction.
        """
        if self._cached_quantifier is None:
            self._compute_target()
        return self._cached_quantifier

    @property
    def target(self):
        """The target ontology class or datatype.

        Returns:
            Union[OntologyClass, UriRef]: The target class or datatype.
        """
        if self._cached_target is None:
            self._compute_target()
        return self._cached_target

    @property
    def relationship(self):
        """The relationship the RELATIONSHIP_RESTRICTION acts on.

        Raises:
            AttributeError: Called on an ATTRIBUTE_RESTRICTION.

        Returns:
            OntologyRelationship: The relationship the restriction acts on.
        """
        if self.rtype == RTYPE.ATTRIBUTE_RESTRICTION:
            raise AttributeError
        return self._property

    @property
    def attribute(self):
        """The attribute the restriction acts on.

        Only for ATTRIBUTE_RESTRICTIONs.

        Raises:
            AttributeError: self is a RELATIONSHIP_RESTRICTIONs.

        Returns:
            UriRef: The datatype of the attribute.
        """
        if self.rtype == RTYPE.RELATIONSHIP_RESTRICTION:
            raise AttributeError
        return self._property

    @property
    def rtype(self):
        """Return the type of restriction.

        Whether the restriction acts on attributes or relationships.

        Returns:
            RTYPE: The type of restriction.
        """
        if self._cached_type is None:
            self._compute_rtype()
        return self._cached_type

    @property
    def _property(self):
        """The relationship or attribute the restriction acts on.

        Returns:
            Union[OntologyRelationship, OntologyAttribute]:
                object of owl:onProperty predicate.
        """
        if self._cached_property is None:
            self._compute_property()
        return self._cached_property

    def _compute_rtype(self):
        """Compute whether this restriction acts on rels or attrs."""
        x = self._property
        if isinstance(x, OntologyRelationship):
            self._cached_type = RTYPE.RELATIONSHIP_RESTRICTION
            return True
        if isinstance(x, OntologyAttribute):
            self._cached_type = RTYPE.ATTRIBUTE_RESTRICTION
            return True

    def _compute_property(self):
        """Compute the object of the OWL:onProperty predicate."""
        x = self._graph.value(self._bnode, rdflib.OWL.onProperty)
        if x and not isinstance(x, BNode):
            self._cached_property = self._namespace_registry.from_iri(x)
            return True

    def _compute_target(self):
        """Compute the target class or datatype."""
        for rdflib_predicate, quantifier in [
            (rdflib.OWL.someValuesFrom, QUANTIFIER.SOME),
            (rdflib.OWL.allValuesFrom, QUANTIFIER.ONLY),
            (rdflib.OWL.cardinality, QUANTIFIER.EXACTLY),
            (rdflib.OWL.minCardinality, QUANTIFIER.MIN),
            (rdflib.OWL.maxCardinality, QUANTIFIER.MAX),
            (rdflib.OWL.hasValue, QUANTIFIER.VALUE),
        ]:
            if self._check_quantifier(rdflib_predicate, quantifier):
                return True

    def _check_quantifier(self, rdflib_predicate, quantifier):
        """Check if the restriction uses given quantifier.

        The quantifier is given as rdflib predicate and python enum.
        """
        x = self._graph.value(self._bnode, rdflib_predicate)
        if x:
            self._cached_quantifier = quantifier
            try:
                self._cached_target = (
                    self._namespace_registry.from_bnode(x)
                    if isinstance(x, BNode)
                    else self._namespace_registry.from_iri(x)
                )
            except KeyError:
                self._cached_target = x
            return True


def get_restriction(bnode, namespace_registry):
    """Return the restriction object represented by given bnode (or None)."""
    r = Restriction(bnode, namespace_registry)
    if r.rtype and r.target:
        return r
