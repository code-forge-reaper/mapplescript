from .expression import Expression
from .serialize import serialize_list

class LambdaDecl(Expression):
    def __init__(self, parameters, body, file, line, column):
        super().__init__("LambdaDecl", file, line, column)
        self.parameters = parameters
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        params = "[" + ", ".join(str(p) for p in self.parameters) + "]"
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"LambdaDecl(parameters={params}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["parameters"] = serialize_list(self.parameters)
        base["body"] = serialize_list(self.body)
        return base
