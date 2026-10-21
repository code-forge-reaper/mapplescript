from .binaryExpr import BinaryExpr

class PipeExpr(BinaryExpr):
    def __init__(self, left, right, file, line, column):
        super().__init__("->", left, right, file, line, column)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"PipeExpr(left={self.left}, right={self.right})"
