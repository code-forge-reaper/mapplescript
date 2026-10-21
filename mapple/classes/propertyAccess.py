from .expression import Expression
from .serialize import serialize_node

class PropertyAccess(Expression):
    def __init__(self, object, property, file, line, column):
        super().__init__("PropertyAccess", file, line, column)
        self.object = object
        self.property = property

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"PropertyAccess(object={self.object}, property='{self.property}')"

    def to_dict(self):
        base = super().to_dict()
        base["object"] = serialize_node(self.object)
        base["property"] = self.property
        return base
