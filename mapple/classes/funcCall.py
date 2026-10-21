from .expression import Expression
from .serialize import serialize_node, serialize_list


class FuncCall(Expression):
    def __init__(self, callee, arguments, file, line, column):
        super().__init__("FuncCall", file, line, column)
        self.callee = callee  # Expression (Identifier, ArrayAccess, etc.)
        self.arguments = arguments

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"FuncCall(callee={self.callee}, arguments={self._str_args()})"

    def _str_args(self):
        return "[" + ", ".join(str(a) for a in self.arguments) + "]"

    @property
    def name(self):
        """Convenience for call-stack / error messages when callee is an Identifier."""
        return getattr(self.callee, "name", "<call>")

    def to_dict(self):
        base = super().to_dict()
        base["callee"] = serialize_node(self.callee)
        base["arguments"] = serialize_list(self.arguments)
        return base
