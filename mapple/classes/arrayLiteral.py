from .expression import Expression
from .serialize import serialize_list

class ArrayLiteral(Expression):
    def __init__(self, elements, file, line, column):
        super().__init__("ArrayLiteral", file, line, column)
        self.elements = elements

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ArrayLiteral(elements={self._str_elements()})"

    def _str_elements(self):
        return "[" + ", ".join(str(e) for e in self.elements) + "]"

    def to_dict(self):
        base = super().to_dict()
        base["elements"] = serialize_list(self.elements)
        return base
