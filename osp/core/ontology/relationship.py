from osp.core.ontology.entity import OntologyEntity
import logging
import rdflib

logger = logging.getLogger(__name__)

# TODO characteristics


class OntologyRelationship(OntologyEntity):
    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        super().__init__(namespace_registry, namespace_iri, name, iri_suffix)
        logger.debug("Create ontology object property %s" % self)

    @property
    def inverse(self):
        """Get the inverse of this relationship.
        If it doesn't exist, add one to the graph.

        Returns:
            OntologyRelationship: The inverse relationship.
        """
        triple1 = (self.iri, rdflib.OWL.inverseOf, None)
        triple2 = (None, rdflib.OWL.inverseOf, self.iri)
        for _, _, o in self.namespace._graph.triples(triple1):
            return self._namespace_registry.from_iri(o)
        for s, _, _ in self.namespace._graph.triples(triple2):
            return self._namespace_registry.from_iri(s)
        return self._add_inverse()

    def _direct_superclasses(self):
        """Get all the direct subclasses of this relationship.

        Returns:
            OntologyRelationship: The direct subrelationships
        """
        return self._directly_connected(rdflib.RDFS.subPropertyOf)

    def _direct_subclasses(self):
        """Get all the direct subclasses of this relationship.

        Returns:
            OntologyRelationship: The direct subrelationships
        """
        return self._directly_connected(rdflib.RDFS.subPropertyOf,
                                        inverse=True)

    def _superclasses(self):
        """Get all the superclasses of this relationship.

        Yields:
            OntologyRelationship: The superrelationships.
        """
        yield self
        yield from self._transitive_hull(rdflib.RDFS.subPropertyOf)

    def _subclasses(self):
        """Get all the subclasses of this relationship.

        Yields:
            OntologyRelationship: The subrelationships.
        """
        yield self
        yield from self._transitive_hull(rdflib.RDFS.subPropertyOf,
                                         inverse=True)

    def _add_inverse(self):
        """Add the inverse of this relationship to the path.

        Returns:
            OntologyRelationship: The inverse relationship.
        """
        o = rdflib.URIRef(self.namespace.get_iri() + "INVERSE_OF_" + self.name)
        x = (self.iri, rdflib.OWL.inverseOf, o)
        y = (o, rdflib.RDF.type, rdflib.OWL.ObjectProperty)

        self.namespace._graph.add(x)
        self.namespace._graph.add(y)
        for superclass in self.direct_superclasses:
            self.namespace._graph.add((
                o, rdflib.RDFS.subPropertyOf, superclass.inverse.iri
            ))
        return self._namespace_registry.from_iri(o)
