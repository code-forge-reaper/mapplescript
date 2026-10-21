from .serialize import serialize_node, serialize_list
from .statement import Statement

class ForStmt(Statement):
    def __init__(self, variable, start, end, step, body, file, line, column):
        super().__init__("ForStmt", file, line, column)
        self.variable = variable
        self.start = start
        self.end = end
        self.step = step
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        step_str = f", step={self.step}" if self.step else ""
        body_str = "[" + ", ".join(str(s) for s in self.body) + "]"
        return f"ForStmt(variable='{self.variable}', start={self.start}, end={self.end}{step_str}, body={body_str})"

    def to_dict(self):
        base = super().to_dict()
        base["variable"] = self.variable
        base["start"] = serialize_node(self.start)
        base["end"] = serialize_node(self.end)
        base["step"] = serialize_node(self.step) if self.step else None
        base["body"] = serialize_list(self.body)
        return base

