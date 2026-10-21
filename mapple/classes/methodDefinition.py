from .serialize import serialize_list
from .statement import Statement

class MethodDefinition(Statement):
    def __init__(
        self,
        name,
        parameters,
        body,
        is_static,
        is_constructor,
        is_private,
        file,
        line,
        column,
    ):
        super().__init__("MethodDefinition", file, line, column)
        self.name = name
        self.parameters = parameters
        self.body = body
        self.is_static = is_static
        self.is_constructor = is_constructor
        self.is_private = is_private

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        params = "[" + ", ".join(str(p) for p in self.parameters) + "]"
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"MethodDefinition(name='{self.name}', parameters={params}, body={body_str}, is_static={self.is_static}, is_constructor={self.is_constructor}, is_private={self.is_private})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = "init" if self.is_constructor else self.name
        base["parameters"] = serialize_list(self.parameters)
        base["body"] = serialize_list(self.body)
        base["is_static"] = self.is_static
        base["is_constructor"] = self.is_constructor
        base["is_private"] = self.is_private
        return base

