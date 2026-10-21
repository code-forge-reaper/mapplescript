from .expression import Expression
from .serialize import serialize_node, serialize_list

class MethodCall(Expression):
    def __init__(self, object, method, arguments, file, line, column):
        super().__init__("MethodCall", file, line, column)
        self.object = object
        self.method = method
        self.arguments = arguments

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"MethodCall(object={self.object}, method='{self.method}', arguments={self._str_args()})"

    def _str_args(self):
        return "[" + ", ".join(str(a) for a in self.arguments) + "]"

    def to_dict(self):
        base = super().to_dict()
        base["object"] = serialize_node(self.object)
        base["method"] = self.method
        base["arguments"] = serialize_list(self.arguments)
        return base
