class PropertyDefinition(Statement):
    def __init__(
        self,
        name,
        type_annotation,
        initializer,
        is_static,
        is_private,
        is_const,
        file,
        line,
        column,
    ):
        super().__init__("PropertyDefinition", file, line, column)
        self.name = name
        self.type_annotation = type_annotation
        self.initializer = initializer
        self.is_static = is_static
        self.is_private = is_private
        self.is_const = is_const

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        type_str = (
            f", type_annotation={self.type_annotation}" if self.type_annotation else ""
        )
        init_str = f", initializer={self.initializer}" if self.initializer else ""
        flags = f", is_static={self.is_static}, is_private={self.is_private}, is_const={self.is_const}"
        return f"PropertyDefinition(name='{self.name}'{type_str}{init_str}{flags})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["type_annotation"] = self.type_annotation
        base["initializer"] = (
            _serialize_node(self.initializer) if self.initializer else None
        )
        base["is_static"] = self.is_static
        base["is_private"] = self.is_private
        base["is_const"] = self.is_const
        return base
