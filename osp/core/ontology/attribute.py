# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.datatypes import convert_from, convert_to
import logging
import rdflib

logger = logging.getLogger(__name__)


class OntologyAttribute(OntologyEntity):
    def __init__(self, namespace, name):
        super().__init__(namespace, name)
        logger.debug("Created ontology data property %s" % self)

    @property
    def name(self):
        return super().name

    @property
    def argname(self):
        return super().name.lower()

    @property
    def datatype(self):
        superclasses = self.superclasses
        datatypes = set()
        for superclass in superclasses:
            triple = (self.iri, rdflib.RDFS.range, None)
            for _, _, o in self.namespace._graph.triples(triple):
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
        return self._directly_connected(rdflib.OWL.subDataPropertyOf)

    def _direct_subclasses(self):
        return self._directly_connected(rdflib.OWL.subDataPropertyOf,
                                        inverse=True)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(rdflib.OWL.subDataPropertyOf)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(rdflib.OWL.subDataPropertyOf,
                                         inverse=True)
