from .serialize import serialize_node
from .statement import Statement

class AssertStmt(Statement):
    def __init__(self, expression, message, file, line, column):
        super().__init__("AssertStmt", file, line, column)
        self.expression = expression
        self.message = message

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        msg_str = f", message='{self.message}'" if self.message else ""
        return f"AssertStmt(expression={self.expression}{msg_str})"

    def to_dict(self):
        base = super().to_dict()
        base["expression"] = serialize_node(self.expression)
        base["message"] = self.message
        return base
