# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.ontology.class_expression import ClassExpression


class RelationshipClassExpression(ClassExpression):
    def __init__(self, relationship, range, cardinality, exclusive):
        self.relationship = relationship
        self.cardinality = cardinality
        self.exclusive = bool(exclusive)

        if not isinstance(range, ClassExpression):
            raise TypeError("Expected ClassExpression as range not %s" % range)

        self.range = range

    def __str__(self):
        pattern = "%s exclusively %s %s" if self.exclusive else "%s %s %s"
        return pattern % (self.relationship, self.cardinality, self.range)
