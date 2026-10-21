class IfStmt(Statement):
    def __init__(self, condition, then_block, else_block, else_if, file, line, column):
        super().__init__("IfStmt", file, line, column)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
        self.else_if = else_if  # list of {"condition": ..., "body": ...}

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        then_str = "[" + ", ".join(str(s) for s in self.then_block) + "]"
        else_if_str = ""
        if self.else_if:
            else_if_str = (
                ", else_if=["
                + ", ".join(
                    f"{{condition={b['condition']}, body=[{', '.join(str(s) for s in b['body'])}]}}"
                    for b in self.else_if
                )
                + "]"
            )
        else_str = ""
        if self.else_block:
            else_str = (
                ", else_block=[" + ", ".join(str(s) for s in self.else_block) + "]"
            )
        return f"IfStmt(condition={self.condition}, then_block={then_str}{else_if_str}{else_str})"

    def to_dict(self):
        base = super().to_dict()
        base["condition"] = _serialize_node(self.condition)
        base["then_block"] = _serialize_list(self.then_block)
        base["else_if"] = (
            [
                {
                    "condition": _serialize_node(b["condition"]),
                    "body": _serialize_list(b["body"]),
                }
                for b in self.else_if
            ]
            if self.else_if
            else []
        )
        base["else_block"] = (
            _serialize_list(self.else_block) if self.else_block else None
        )
        return base

