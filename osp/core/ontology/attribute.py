from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.datatypes import convert_from, convert_to
import logging
import rdflib

logger = logging.getLogger(__name__)


class OntologyAttribute(OntologyEntity):
    def __init__(self, namespace, name, iri_suffix):
        super().__init__(namespace, name, iri_suffix)
        logger.debug("Created ontology data property %s" % self)

    @property
    def name(self):
        return super().name

    @property
    def argname(self):
        return super().name

    @property
    def datatype(self):
        """Get the datatype of the attribute

        Raises:
            RuntimeError: More than one datatype associated with the attribute.
            # TODO should be allowed

        Returns:
            URIRef: IRI of the datatype
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
        raise RuntimeError(f"More than one datatype associated to {self}:"
                           f" {datatypes}")

    def convert_to_datatype(self, value):
        """Convert to the datatype of the value

        :param value: The value to convert
        :type value: Any
        :return: The converted value
        :rtype: Any
        """
        return convert_to(value, self.datatype)

    def convert_to_basic_type(self, value):
        """Convert from the datatype of the value to a python basic type

        :param value: The value to convert
        :type value: Any
                :return: The converted value
        :rtype: Any
        """
        return convert_from(value, self.datatype)

    def _direct_superclasses(self):
        return self._directly_connected(rdflib.RDFS.subPropertyOf)

    def _direct_subclasses(self):
        return self._directly_connected(rdflib.RDFS.subPropertyOf,
                                        inverse=True)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(
            rdflib.RDFS.subPropertyOf,
            blacklist={rdflib.OWL.bottomDataProperty,
                       rdflib.OWL.topDataProperty})

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(
            rdflib.RDFS.subPropertyOf, inverse=True,
            blacklist={rdflib.OWL.bottomDataProperty,
                       rdflib.OWL.topDataProperty})
