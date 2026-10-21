from .statement import Statement

class BreakStmt(Statement):
    def __init__(self, file, line, column):
        super().__init__("BreakStmt", file, line, column)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "BreakStmt()"

