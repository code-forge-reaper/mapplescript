from .expression import Expression
from .serialize import serialize_node

class AssignmentExpr(Expression):
    def __init__(self, target, value, operator, file, line, column):
        super().__init__("AssignmentExpr", file, line, column)
        self.target = target
        self.value = value
        self.operator = operator

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"AssignmentExpr(target={self.target}, value={self.value}, operator='{self.operator}')"

    def to_dict(self):
        base = super().to_dict()
        base["target"] = serialize_node(self.target)
        base["value"] = serialize_node(self.value)
        base["operator"] = self.operator
        return base
