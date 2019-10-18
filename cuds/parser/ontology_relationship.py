# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.parser.ontology_entity import OntologyEntity


class OntologyRelationship(OntologyEntity):
    def __init__(self, name, superclasses, yaml_def):
        super().__init__(name, superclasses, yaml_def)
