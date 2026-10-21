
class TryStmt(Statement):
    def __init__(self, try_block, error_var, catch_block, file, line, column):
        super().__init__("TryStmt", file, line, column)
        self.try_block = try_block
        self.error_var = error_var
        self.catch_block = catch_block

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        try_str = "[" + ", ".join(str(s) for s in self.try_block) + "]"
        catch_str = "[" + ", ".join(str(s) for s in self.catch_block) + "]"
        return f"TryStmt(try_block={try_str}, error_var='{self.error_var}', catch_block={catch_str})"

    def to_dict(self):
        base = super().to_dict()
        base["try_block"] = _serialize_list(self.try_block)
        base["error_var"] = self.error_var
        base["catch_block"] = _serialize_list(self.catch_block)
        return base

