from .serialize import serialize_node
from .statement import Statement

class ReturnStmt(Statement):
    def __init__(self, expression, file, line, column):
        super().__init__("ReturnStmt", file, line, column)
        self.expression = expression

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        expr_str = f", expression={self.expression}" if self.expression else ""
        return f"ReturnStmt({expr_str})"

    def to_dict(self):
        base = super().to_dict()
        base["expression"] = (
            serialize_node(self.expression) if self.expression else None
        )
        return base

