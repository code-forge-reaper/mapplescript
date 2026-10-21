from .serialize import serialize_list
from .statement import Statement

class ClassDefinition(Statement):
    def __init__(self, name, superclass_name, body, file, line, column):
        super().__init__("ClassDefinition", file, line, column)
        self.name = name
        self.superclass_name = superclass_name
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        super_str = (
            f", superclass='{self.superclass_name}'" if self.superclass_name else ""
        )
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"ClassDefinition(name='{self.name}'{super_str}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["class_name"] = self.name
        base["superclass"] = self.superclass_name
        base["body"] = serialize_list(self.body)
        return base

