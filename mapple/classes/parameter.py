from .serialize import serialize_node
from .baseToken import Token

class Parameter(Token):
    def __init__(
        self,
        name,
        annotation_type,
        default,
        is_compact,
        file,
        line,
        column,
        type,
        value,
    ):
        super().__init__(type, value, file, line, column)
        self.name = name
        self.annotation_type = annotation_type
        self.default = default
        self.is_compact = is_compact

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        default_str = f", default={self.default}" if self.default is not None else ""
        return f"Parameter(name='{self.name}', annotation_type={self.annotation_type}{default_str}, is_compact={self.is_compact})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["annotation_type"] = self.annotation_type
        base["default"] = serialize_node(self.default) if self.default else None
        base["is_compact"] = self.is_compact
        return base
