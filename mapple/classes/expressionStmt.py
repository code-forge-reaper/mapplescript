from .serialize import serialize_node
from .statement import Statement

class ExpressionStmt(Statement):
    def __init__(self, expression, file, line, column):
        super().__init__("ExpressionStmt", file, line, column)
        self.expression = expression

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ExpressionStmt(expression={self.expression})"

    def to_dict(self):
        base = super().to_dict()
        base["expression"] = serialize_node(self.expression)
        return base
