class DeferStmt(Statement):
    def __init__(self, body, file, line, column):
        super().__init__("DeferStmt", file, line, column)
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"DeferStmt(body={self._str_body()})"

    def _str_body(self):
        return "[" + ", ".join(str(s) for s in self.body) + "]"

    def to_dict(self):
        base = super().to_dict()
        base["body"] = _serialize_list(self.body)
        return base
