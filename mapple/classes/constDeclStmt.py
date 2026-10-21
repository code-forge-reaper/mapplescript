from .serialize import serialize_node
from .statement import Statement

class ConstDeclStmt(Statement):
    def __init__(self, name, type_annotation, initializer, file, line, column):
        super().__init__("ConstDecl", file, line, column)
        self.name = name
        self.type_annotation = type_annotation
        self.initializer = initializer

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        type_str = (
            f", type_annotation={self.type_annotation}" if self.type_annotation else ""
        )
        init_str = f", initializer={self.initializer}" if self.initializer else ""
        return f"ConstDeclStmt(name='{self.name}'{type_str}{init_str})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["type_annotation"] = self.type_annotation
        base["initializer"] = serialize_node(self.initializer)
        return base
