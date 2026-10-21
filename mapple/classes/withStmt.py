from .serialize import serialize_node, serialize_list
from .statement import Statement

class WithStmt(Statement):
    def __init__(self, expr, alias, body, file, line, column):
        super().__init__("WithStmt", file, line, column)
        self.expr = expr
        self.alias = alias
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        alias_str = f", alias='{self.alias}'" if self.alias else ""
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"WithStmt(expr={self.expr}{alias_str}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["expression"] = serialize_node(self.expr)
        base["alias"] = self.alias
        base["body"] = serialize_list(self.body)
        return base

