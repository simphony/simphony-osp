"""An attribute defined in the ontology."""

import logging

import rdflib

from osp.core.ontology.datatypes import convert_from, convert_to
from osp.core.ontology.entity import OntologyEntity

logger = logging.getLogger(__name__)


BLACKLIST = {rdflib.OWL.bottomDataProperty, rdflib.OWL.topDataProperty}


class OntologyAttribute(OntologyEntity):
    """An attribute defined in the ontology."""

    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        """Initialize the ontology attribute.

        Args:
            namespace_registry (OntologyNamespaceRegistry): The namespace
                registry where all namespaces are stored.
            namespace_iri (rdflib.URIRef): The IRI of the namespace.
            name (str): The name of the attribute.
            iri_suffix (str): namespace_iri +  namespace_registry make up the
                namespace of this entity.
        """
        super().__init__(namespace_registry, namespace_iri, name, iri_suffix)
        logger.debug("Created ontology data property %s" % self)

    @property
    def argname(self):
        """Get the name of the attribute when used as an argument.

        This name is used when construction a cuds object or accessing
        the attributes of a CUDS object.
        """
        return super().name

    @property
    def datatype(self):
        """Get the datatype of the attribute.

        Returns:
            URIRef: IRI of the datatype

        Raises:
            RuntimeError: More than one datatype associated with the attribute.
                # TODO should be allowed
        """
        blacklist = [rdflib.RDFS.Literal]
        superclasses = self.superclasses
        datatypes = set()
        for superclass in superclasses:
            triple = (superclass.iri, rdflib.RDFS.range, None)
            for _, _, o in self.namespace._graph.triples(triple):
                if o not in blacklist:
                    datatypes.add(o)
        if len(datatypes) == 1:
            return datatypes.pop()
        if len(datatypes) == 0:
            return None
        raise RuntimeError(
            f"More than one datatype associated to {self}:" f" {datatypes}"
        )

    def convert_to_datatype(self, value):
        """Convert to the datatype of the value.

        Args:
            value(Any): The value to convert

        Returns:
            Any: The converted value
        """
        return convert_to(value, self.datatype)

    def convert_to_basic_type(self, value):
        """Convert from the datatype of the value to a python basic type.

        Args:
            value(Any): The value to convert

        Returns:
            Any: The converted value
        """
        return convert_from(value, self.datatype)

    def _direct_superclasses(self):
        return self._directly_connected(
            rdflib.RDFS.subPropertyOf, blacklist=BLACKLIST
        )

    def _direct_subclasses(self):
        return self._directly_connected(
            rdflib.RDFS.subPropertyOf, inverse=True, blacklist=BLACKLIST
        )

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(
            rdflib.RDFS.subPropertyOf, blacklist=BLACKLIST
        )

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(
            rdflib.RDFS.subPropertyOf, inverse=True, blacklist=BLACKLIST
        )
