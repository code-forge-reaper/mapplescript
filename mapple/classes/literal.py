from .expression import Expression

# --- Specific AST Node Classes ---
class Literal(Expression):
    def __init__(self, value, file, line, column):
        super().__init__("Literal", file, line, column)
        self.value = value

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Literal(value={repr(self.value)})"

    def to_dict(self):
        base = super().to_dict()
        base["literal_value"] = self.value
        return base
