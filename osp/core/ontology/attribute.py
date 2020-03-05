# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.datatypes import (
    ONTOLOGY_DATATYPES, convert_from, convert_to
)
import logging
import rdflib

logger = logging.getLogger(__name__)


CONFLICTING = "2L4N4lGLYBU8mBNx8H6X6dC6Mcf2AcBqIKnFnXUI"


class OntologyAttribute(OntologyEntity):
    def __init__(self, namespace, name, superclasses, description):
        super().__init__(namespace, name, superclasses, description)
        self._datatype = None

    @property
    def name(self):
        return super().name

    @property
    def argname(self):
        return super().name.lower()

    @property
    def datatype(self):
        result = self._get_datatype_recursively()
        if result == CONFLICTING:
            logger.warning("Conflicting datatype for %s" % self)
            return "UNDEFINED"
        return result or "UNDEFINED"

    # OVERRIDE
    def get_triples(self):
        return super().get_triples() + [
            (self.iri, rdflib.RDFS.subPropertyOf, x.iri)
            for x in self.superclasses
        ] + [
            (self.iri, rdflib.RDF.type, rdflib.OWL.DataProperty),
        ]

    def _get_datatype_recursively(self):
        """Get the datatype of the value

        :return: The datatype of the ontology value
        :rtype: str
        """
        if self._datatype is not None:
            return self._datatype  # datatype is defined

        # check for inherited datatype
        datatype = None
        for p in self.direct_superclasses:
            if not isinstance(p, OntologyAttribute):
                continue
            superclass_datatype = p._get_datatype_recursively()
            if (
                datatype is not None
                and superclass_datatype is not None
                and datatype != superclass_datatype
            ):
                return CONFLICTING  # conflicting datatypes of superclasses
            datatype = datatype or superclass_datatype
        return datatype

    def __call__(self, value):
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

    def _set_datatype(self, datatype):
        """Set the datatype of the value

        :param datatype: The datatype of the value
        :type datatype: str
        """
        if datatype.split(":")[0] not in ONTOLOGY_DATATYPES:
            raise ValueError("Invalid datatype %s specified for %s"
                             % (datatype, self))
        self._datatype = datatype
