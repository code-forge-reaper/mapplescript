from .serialize import serialize_node, serialize_list
from .statement import Statement

class WhileStmt(Statement):
    def __init__(self, condition, body, file, line, column):
        super().__init__("WhileStmt", file, line, column)
        self.condition = condition
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"WhileStmt(condition={self.condition}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["condition"] = serialize_node(self.condition)
        base["body"] = serialize_list(self.body)
        return base

