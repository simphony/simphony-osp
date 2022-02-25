"""Catalog of ontology entities available in SimPhoNy."""

from simphony_osp.core.ontology.annotation import OntologyAnnotation
from simphony_osp.core.ontology.attribute import OntologyAttribute
from simphony_osp.core.ontology.entity import OntologyEntity
from simphony_osp.core.ontology.individual import OntologyIndividual
from simphony_osp.core.ontology.interactive.container import Container
from simphony_osp.core.ontology.interactive.file import File
from simphony_osp.core.ontology.namespace import OntologyNamespace
from simphony_osp.core.ontology.oclass import OntologyClass
from simphony_osp.core.ontology.oclass_composition import Composition
from simphony_osp.core.ontology.oclass_restriction import Restriction
from simphony_osp.core.ontology.relationship import OntologyRelationship

__all__ = ['Composition', 'Container', 'File', 'Restriction',
           'OntologyAnnotation', 'OntologyAttribute', 'OntologyEntity',
           'OntologyIndividual', 'OntologyNamespace', 'OntologyClass',
           'OntologyRelationship']
