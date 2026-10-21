from .serialize import serialize_list
from .expression import Expression

class ExplodeExpr(Expression):
    def __init__(self, args, file, line, col):
        super().__init__("ExplodeExpr", file, line, col)
        self.args = args

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"ExplodeExpr(args={self._str_args()})"

    def _str_args(self):
        return "[" + ", ".join(str(a) for a in self.args) + "]"

    def to_dict(self):
        base = super().to_dict()
        base["args"] = serialize_list(self.args)
        return base
