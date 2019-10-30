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


class OntologyValue(OntologyEntity):
    def __init__(self, namespace, name, superclasses, definition):
        super().__init__(namespace, name, superclasses, definition)
        self._datatype = None

    @property
    def name(self):
        return super().name.lower()

    @property
    def datatype(self):
        """Get the datatype of the value

        :return: The datatype of the ontology value
        :rtype: str
        """
        if self._datatype is not None:
            return self._datatype  # datatype is defined

        # check for inherited datatype
        datatype = None
        for p in self.direct_superclasses:
            if not isinstance(p, OntologyValue):
                continue
            superclass_datatype = p.datatype
            if datatype is not None and superclass_datatype is not None:
                return "UNDEFINED"  # conflicting datatypes of superclasses
            datatype = datatype or superclass_datatype

        if datatype is None:
            return "UNDEFINED"  # undefined datatype
        return datatype

    def __call__(self, value):
        """Convert to the datatype of the value

        :param value: The value to convert
        :type value: Any
        :return: The converted value
        :rtype: Any
        """
        return convert_to(value)

    def convert_to_basic_type(self, value):
        """Convert from the datatype of the value to a python basic type

        :param value: The value to convert
        :type value: Any
                :return: The converted value
        :rtype: Any
        """
        return convert_from(value)

    def _set_datatype(self, datatype):
        """Set the datatype of the value

        :param datatype: The datatype of the value
        :type datatype: str
        """
        assert datatype.split(":")[0] in ONTOLOGY_DATATYPES
        self._datatype = datatype
