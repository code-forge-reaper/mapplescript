from .serialize import serialize_node
from .expression import Expression

class NamedArg(Expression):
    """Represents a named / keyword argument at a call site: name: value"""

    def __init__(self, name, value, file, line, column):
        super().__init__("NamedArg", file, line, column)
        self.name = name
        self.value = value

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"NamedArg(name='{self.name}', value={self.value})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["value"] = serialize_node(self.value)
        return base
