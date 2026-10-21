class FuncDecl(Statement):
    def __init__(self, name, parameters, body, file, line, column):
        super().__init__("FuncDecl", file, line, column)
        self.name = name
        self.parameters = parameters
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        params = "[" + ", ".join(str(p) for p in self.parameters) + "]"
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"FuncDecl(name='{self.name}', parameters={params}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["name"] = self.name
        base["parameters"] = _serialize_list(self.parameters)
        base["body"] = _serialize_list(self.body)
        return base
