from .expression import Expression


class ObjectLiteral(Expression):
    def __init__(self, properties, file, line, column):
        super().__init__("ObjectLiteral", file, line, column)
        self.properties = properties  # list of dicts with 'key' and 'value'

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        props = []
        for p in self.properties:
            key = p["key"] if isinstance(p["key"], str) else str(p["key"])
            props.append(f"{key}: {p['value']}")
        return f"ObjectLiteral(properties={{{', '.join(props)}}})"

    def to_dict(self):
        base = super().to_dict()
        props = []
        for p in self.properties:
            props.append(
                {
                    "key": p["key"]
                    if isinstance(p["key"], str)
                    else _serialize_node(p["key"]),
                    "value": _serialize_node(p["value"]),
                }
            )
        base["properties"] = props
        return base
