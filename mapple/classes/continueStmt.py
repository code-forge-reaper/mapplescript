from .statement import Statement

class ContinueStmt(Statement):
    def __init__(self, file, line, column):
        super().__init__("ContinueStmt", file, line, column)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "ContinueStmt()"
