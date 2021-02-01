from enum import Enum
import rdflib
import logging
from rdflib.term import BNode
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.relationship import OntologyRelationship

logger = logging.getLogger(__name__)


class QUANTIFIER(Enum):
    SOME = 1
    ONLY = 2
    EXACTLY = 3
    MIN = 4
    MAX = 5


class TYPE(Enum):
    ATTRIBUTE_RESTRICTION = 1
    RELATIONSHIP_RESTRICTION = 2


class Restriction():
    def __init__(self, bnode, graph, namespace_registry):
        self._bnode = bnode
        self._graph = graph
        self._namespace_registry = namespace_registry
        self._cached_quantifier = None
        self._cached_property = None
        self._cached_target = None
        self._cached_type = None

    @property
    def quantifier(self):
        if self._cached_quantifier is None:
            self._compute_target()
        return self._cached_quantifier

    @property
    def target(self):
        if self._cached_target is None:
            self._compute_target()
        return self._cached_target

    @property
    def relationship(self):
        if self.rtype == TYPE.ATTRIBUTE_RESTRICTION:
            raise AttributeError
        return self._property

    @property
    def attribute(self):
        if self.rtype == TYPE.RELATIONSHIP_RESTRICTION:
            raise AttributeError
        return self._property

    @property
    def rtype(self):
        if self._cached_type is None:
            self._compute_rtype()
        return self._cached_type

    @property
    def _property(self):
        if self._cached_property is None:
            self._compute_property()
        return self._cached_property

    def _compute_rtype(self):
        x = self._property
        if isinstance(x, OntologyRelationship):
            self._cached_type = TYPE.RELATIONSHIP_RESTRICTION
            return True
        if isinstance(x, OntologyAttribute):
            self._cached_type = TYPE.ATTRIBUTE_RESTRICTION
            return True
        self._print_warning()

    def _compute_property(self):
        x = self._graph.value(self._bnode, rdflib.OWL.onProperty)
        if x and not isinstance(x, BNode):
            self._cached_property = self._namespace_registry.from_iri(x)
            return True
        self._print_warning()

    def _compute_target(self):
        for rdflib_predicate, quantifier in [
            (rdflib.OWL.someValuesFrom, QUANTIFIER.SOME),
            (rdflib.OWL.allValuesFrom, QUANTIFIER.ONLY),
            (rdflib.OWL.cardinality, QUANTIFIER.EXACTLY),
            (rdflib.OWL.minCardinality, QUANTIFIER.MIN),
            (rdflib.OWL.maxCardinality, QUANTIFIER.MAX)
        ]:
            if self._check_quantifier(rdflib_predicate, quantifier):
                return
        self._print_warning()

    def _check_quantifier(self, rdflib_predicate, quantifier):
        x = self._graph.value(self._bnode, rdflib_predicate)
        if x and not isinstance(x, BNode):
            self._cached_quantifier = quantifier
            try:
                self._cached_target = self._namespace_registry.from_iri(x)
            except KeyError:
                self._cached_target = x
            return True

    def _print_warning(self):
        logger.debug("Unsupported restriction encountered.")
        logger.debug("Defined by the following triples:")
        for s, p, o in self._graph.triples((self._bnode, None, None)):
            logger.debug(f"{s}\n\t{p}\n\t{o}")
        # for s, p, o in self._graph.triples((None, None, self._bnode)):
        #     logger.warning(f"{s}\n\t{p}\n\t{o}")
