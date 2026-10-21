from .expression import Expression


class BinaryExpr(Expression):
    def __init__(self, operator, left, right, file, line, column):
        super().__init__("BinaryExpr", file, line, column)
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"BinaryExpr(operator='{self.operator}', left={self.left}, right={self.right})"

    def to_dict(self):
        base = super().to_dict()
        base["operator"] = self.operator
        base["left"] = _serialize_node(self.left)
        base["right"] = _serialize_node(self.right)
        return base
