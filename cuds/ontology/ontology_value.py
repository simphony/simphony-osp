# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.parser import DATATYPE_KEY
from cuds.parser.ontology_entity import OntologyEntity


class OntologyValue(OntologyEntity):
    def __init__(self, name, superclasses, yaml_def):
        super().__init__(name, superclasses, yaml_def)
        self._datatype = None
        if DATATYPE_KEY in yaml_def:
            self._datatype = yaml_def[DATATYPE_KEY]

    def get_datatype(self):
        """Get the datatype of the value

        :return: The datatype of the ontology value
        :rtype: str
        """
        if self._datatype is not None:
            return self._datatype  # datatype is defined

        # check for inherited datatype
        datatype = None
        for p in self.get_direct_superclasses():
            superclass_datatype = p.get_datatype()
            if datatype is not None and superclass_datatype is not None:
                return "UNDEFINED"  # conflicting datatypes of superclasses
            datatype = datatype or superclass_datatype

        if datatype is None:
            return "UNDEFINED"  # undefined datatype
        return datatype
