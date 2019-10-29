# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.ontology.ontology_entity import OntologyEntity


class OntologyRelationship(OntologyEntity):
    def __init__(self, name, superclasses, definition):
        super().__init__(name, superclasses, definition)
        self.inverse = None

    def _set_inverse(self, inverse):
        assert isinstance(inverse, OntologyRelationship)
        self.inverse = inverse
