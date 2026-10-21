from .expression import Expression


class Identifier(Expression):
    def __init__(self, name, file, line, column):
        super().__init__("Identifier", file, line, column)
        self.name = name

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Identifier(name='{self.name}')"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        return base
