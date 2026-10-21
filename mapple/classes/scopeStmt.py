from .serialize import serialize_list
from .statement import Statement

class ScopeStmt(Statement):
    def __init__(self, name, body, file, line, column):
        super().__init__("ScopeStmt", file, line, column)
        self.name = name
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"ScopeStmt(name='{self.name}', body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["body"] = serialize_list(self.body)
        return base

