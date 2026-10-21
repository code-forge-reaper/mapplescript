class LocalFuncDecl(Statement):
    def __init__(self, fn, file, line, column):
        super().__init__("LocalFuncDecl", file, line, column)
        self.fn = fn

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"LocalFuncDecl(fn={self.fn})"

    def to_dict(self):
        base = super().to_dict()
        base["function"] = _serialize_node(self.fn)
        return base
