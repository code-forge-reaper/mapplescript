class DecoratorExpr(Expression):
    def __init__(self, expr, body, file, line, column):
        super().__init__("DecoratorExpr", file, line, column)
        self.expr = expr
        self.body = body

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"DecoratorExpr(expr={self.expr}, body={self.body})"

    def to_dict(self):
        base = super().to_dict()
        base["expr"] = _serialize_node(self.expr)
        base["body"] = _serialize_node(self.body)
        return base
