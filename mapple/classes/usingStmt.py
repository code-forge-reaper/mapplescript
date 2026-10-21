from .statement import Statement


class UsingStmt(Statement):
    def __init__(self, name, file, line, column):
        super().__init__("UsingStmt", file, line, column)
        self.name = name

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if isinstance(self.name, list):
            names = "[" + ", ".join(f"'{n}'" for n in self.name) + "]"
            return f"UsingStmt(names={names})"
        return f"UsingStmt(name='{self.name}')"

    def to_dict(self):
        base = super().to_dict()
        if isinstance(self.name, list):
            base["names"] = self.name
        else:
            base["name"] = self.name
        return base
