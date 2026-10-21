from .serialize import serialize_node, serialize_list

class Case:
    def __init__(self, case_expr, body):
        self.case_expr = case_expr
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Case(case_expr={self.case_expr if self.case_expr else 'default'}, body={self._str_body()})"

    def _str_body(self):
        return "[" + ", ".join(str(s) for s in self.body) + "]"

    def to_dict(self):
        return {
            "type": "Case",
            "case_expr": serialize_node(self.case_expr)
            if self.case_expr
            else "default",
            "body": serialize_list(self.body),
        }

