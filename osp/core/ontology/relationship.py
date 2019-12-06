# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.ontology.entity import OntologyEntity


class OntologyRelationship(OntologyEntity):
    def __init__(self, namespace, name, superclasses, description):
        super().__init__(namespace, name, superclasses, description)
        self._inverse = None

    @property
    def inverse(self):
        return self._inverse

    def _set_inverse(self, inverse):
        if not isinstance(inverse, OntologyRelationship):
            raise TypeError("Tried to add non-relationship %s "
                            "as inverse to %s" % (inverse, self))
        self._inverse = inverse

    @property
    def domain_expressions(self):
        """Get the subclass_of class expressions"""
        from osp.core.ontology.parser import DOMAIN_KEY
        return self._collect_class_expressions(DOMAIN_KEY)

    @property
    def range_expressions(self):
        """Get the subclass_of class expressions"""
        from osp.core.ontology.parser import RANGE_KEY
        return self._collect_class_expressions(RANGE_KEY)
