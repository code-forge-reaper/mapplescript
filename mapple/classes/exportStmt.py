from .serialize import serialize_node
from .statement import Statement

class ExportStmt(Statement):
    def __init__(self, expr, file, line, column):
        super().__init__("ExportStmt", file, line, column)
        self.expr = expr

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ExportStmt(expr={self.expr})"

    def to_dict(self):
        base = super().to_dict()
        base["expression"] = serialize_node(self.expr)
        return base
