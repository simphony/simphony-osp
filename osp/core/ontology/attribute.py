"""An attribute defined in the ontology."""

import logging

from rdflib import OWL, RDFS, XSD, Literal

from osp.core.ontology.datatypes import RDF_TO_PYTHON
from osp.core.ontology.entity import OntologyEntity


logger = logging.getLogger(__name__)


BLACKLIST = {OWL.bottomDataProperty, OWL.topDataProperty}


class OntologyAttribute(OntologyEntity):
    """An attribute defined in the ontology."""

    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        """Initialize the ontology attribute.

        Args:
            namespace_registry (OntologyNamespaceRegistry): The namespace
                registry where all namespaces are stored.
            namespace_iri (URIRef): The IRI of the namespace.
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
        blacklist = [RDFS.Literal]
        superclasses = self.superclasses
        datatypes = set()
        for superclass in superclasses:
            for o in self.namespace._graph.objects(superclass.iri, RDFS.range):
                if o not in blacklist:
                    datatypes.add(o)
        if len(datatypes) == 1:
            return datatypes.pop()
        if len(datatypes) == 0:
            return None
        raise RuntimeError(f"More than one datatype associated to {self}:"
                           f" {datatypes}")

    def convert_to_datatype(self, value):
        """Convert to the datatype of the value.

        Args:
            value(Any): The value to convert

        Returns:
            Any: The converted value
        """
        # TODO: Very similar to
        #  `osp.core.session.db.sql_wrapper_session.SqlWrapperSession
        #  ._convert_to_datatype`. Unify somehow.
        if isinstance(value, Literal):
            result = Literal(value.toPython(), datatype=self.datatype,
                             lang=value.language).toPython()
            if isinstance(result, Literal):
                result = RDF_TO_PYTHON[self.datatype or XSD.string](
                    value.value)
        else:
            result = RDF_TO_PYTHON[self.datatype or XSD.string](value)
        return result

    def _direct_superclasses(self):
        return self._directly_connected(RDFS.subPropertyOf,
                                        blacklist=BLACKLIST)

    def _direct_subclasses(self):
        return self._directly_connected(RDFS.subPropertyOf,
                                        inverse=True, blacklist=BLACKLIST)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(RDFS.subPropertyOf,
                                         blacklist=BLACKLIST)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(RDFS.subPropertyOf,
                                         inverse=True, blacklist=BLACKLIST)
