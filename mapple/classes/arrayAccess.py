from .expression import Expression
from .serialize import serialize_node

class ArrayAccess(Expression):
    def __init__(self, object, index, file, line, column):
        super().__init__("ArrayAccess", file, line, column)
        self.object = object
        self.index = index

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ArrayAccess(object={self.object}, index={self.index})"

    def to_dict(self):
        base = super().to_dict()
        base["object"] = serialize_node(self.object)
        base["index"] = serialize_node(self.index)
        return base
