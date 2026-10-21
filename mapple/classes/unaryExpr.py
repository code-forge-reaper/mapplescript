from .expression import Expression


class UnaryExpr(Expression):
    def __init__(self, operator, right, file, line, column):
        super().__init__("UnaryExpr", file, line, column)
        self.operator = operator
        self.right = right

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"UnaryExpr(operator='{self.operator}', right={self.right})"

    def to_dict(self):
        base = super().to_dict()
        base["operator"] = self.operator
        base["right"] = _serialize_node(self.right)
        return base
