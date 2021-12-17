"""Catalog of ontology entities available in OSP-core."""

from osp.core.ontology.annotation import OntologyAnnotation
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.individual import OntologyIndividual
from osp.core.ontology.interactive.container import Container
from osp.core.ontology.interactive.file import File
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.oclass_composition import Composition
from osp.core.ontology.oclass_restriction import Restriction
from osp.core.ontology.relationship import OntologyRelationship

__all__ = ['Composition', 'Container', 'File', 'Restriction',
           'OntologyAnnotation', 'OntologyAttribute', 'OntologyEntity',
           'OntologyIndividual', 'OntologyNamespace', 'OntologyClass',
           'OntologyRelationship']
