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
