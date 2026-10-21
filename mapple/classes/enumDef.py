from .expression import Expression

class EnumDef(Expression):
    def __init__(self, values, file, line, column):
        super().__init__("EnumDef", file, line, column)
        self.values = values

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"EnumDef(values={self.values})"

    def to_dict(self):
        base = super().to_dict()
        base["values"] = self.values
        return base
