from .expression import Expression


class NewInstance(Expression):
    def __init__(self, class_name, arguments, file, line, column):
        super().__init__("NewInstance", file, line, column)
        self.class_name = class_name
        self.arguments = arguments

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return (
            f"NewInstance(class_name='{self.class_name}', arguments={self._str_args()})"
        )

    def _str_args(self):
        return "[" + ", ".join(str(a) for a in self.arguments) + "]"

    def to_dict(self):
        base = super().to_dict()
        base["class_name"] = self.class_name
        base["arguments"] = _serialize_list(self.arguments)
        return base
