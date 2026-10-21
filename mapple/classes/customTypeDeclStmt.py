from .statement import Statement

class CustomTypeDeclStmt(Statement):
    def __init__(self, name, definition, file, line, column):
        super().__init__("CustomTypeDeclStmt", file, line, column)
        self.name = name
        self.definition = definition  # list of CustomTypeProperty

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        props = ", ".join(str(p) for p in self.definition)
        return f"CustomTypeDeclStmt(name='{self.name}', properties=[{props}])"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["properties"] = [p.to_dict() for p in self.definition]
        return base
