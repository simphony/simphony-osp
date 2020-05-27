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

    def __str__(self):
        if len(self.operands) > 1:
            return "(%s)" % ((" %s " % self.operator).join([
                str(x) for x in self.operands
            ]))
        return "%s(%s)" % (self.operator, "".join([
            str(x) for x in self.operands
        ]))
