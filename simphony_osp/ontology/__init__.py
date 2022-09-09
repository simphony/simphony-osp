"""Ontology module for the SimPhoNy OSP."""

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.composition import OPERATOR as COMPOSITION_OPERATOR
from simphony_osp.ontology.composition import Composition
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import (
    AnnotationSet,
    AttributeSet,
    MultipleResultsError,
    OntologyIndividual,
    RelationshipSet,
    ResultEmptyError,
)
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.ontology.restriction import (
    QUANTIFIER as RESTRICTION_QUANTIFIER,
)
from simphony_osp.ontology.restriction import RTYPE as RESTRICTION_TYPE
from simphony_osp.ontology.restriction import Restriction

__all__ = [
    "AnnotationSet",
    "AttributeSet",
    "Composition",
    "COMPOSITION_OPERATOR",
    "MultipleResultsError",
    "RESTRICTION_QUANTIFIER",
    "RESTRICTION_TYPE",
    "RelationshipSet",
    "Restriction",
    "ResultEmptyError",
    "OntologyAnnotation",
    "OntologyAttribute",
    "OntologyEntity",
    "OntologyIndividual",
    "OntologyNamespace",
    "OntologyClass",
    "OntologyRelationship",
]
