"""Ontology module for the SimPhoNy OSP."""

from simphony_osp.ontology.annotation import OntologyAnnotation
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.composition import Composition
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.ontology.restriction import Restriction

__all__ = [
    "Composition",
    "Restriction",
    "OntologyAnnotation",
    "OntologyAttribute",
    "OntologyEntity",
    "OntologyIndividual",
    "OntologyNamespace",
    "OntologyClass",
    "OntologyRelationship",
]
