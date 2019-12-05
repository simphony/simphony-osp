# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from osp.core.ontology.class_expression import ClassExpression
from inspect import getfullargspec

OPERATORS = {
    "not": lambda x: not x,
    "and": lambda x, y: x and y,
    "or": lambda x, y: x or y
}


def num_args(operator):
    return len(getfullargspec(OPERATORS[operator]).args)


class OperatorClassExpression(ClassExpression):
    def __init__(self, operator, operands=None):
        if operator not in OPERATORS:
            raise ValueError("Unknown operator %s" % operator)
        self.operator = operator
        self.operands = operands or list()

        # validity checks
        if len(self.operands) != 1 and num_args(self.operator) == 1:
            raise RuntimeError(
                "Given %s class expressions to unary operator %s"
                % (len(self.operands), self.operator)
            )
        for x in self.operands:
            if not isinstance(x, ClassExpression):
                raise TypeError(
                    "Expected ClassExpression as operand not %s" % x
                )

    @property
    def class_expressions(self):
        return self._class_expressions

    @property
    def class_expression(self):
        if num_args(self.operator) != 1:
            raise AttributeError(
                "'class_expression' not defined for %s-ary operator %s"
                % (num_args(self.operator), self.operator)
            )
        return self._class_expressions[0]

    def __str__(self):
        return "(%s)" % ((" %s " % self.operator).join([
            str(x) for x in self.operands
        ]))
