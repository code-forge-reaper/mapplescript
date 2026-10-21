from .serialize import serialize_node
from .statement import Statement

class SwitchStmt(Statement):
    def __init__(self, expression, cases, strict, file, line, column):
        super().__init__("SwitchStmt", file, line, column)
        self.expression = expression
        self.cases = cases
        self.strict = strict

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        cases_str = "[" + ", ".join(str(c) for c in self.cases) + "]"
        return f"SwitchStmt(expression={self.expression}, cases={cases_str}, strict={self.strict})"

    def to_dict(self):
        base = super().to_dict()
        base["expression"] = serialize_node(self.expression)
        base["cases"] = [c.to_dict() for c in self.cases]
        base["strict"] = self.strict
        return base
