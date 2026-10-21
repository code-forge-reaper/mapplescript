class ForEachStmt(Statement):
    def __init__(self, variable, list, body, file, line, column):
        super().__init__("ForEachStmt", file, line, column)
        self.variable = variable
        self.list = list
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"ForEachStmt(variable='{self.variable}', list={self.list}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["variable"] = self.variable
        base["list"] = _serialize_node(self.list)
        base["body"] = _serialize_list(self.body)
        return base
