def Object(self, expr, env):
    obj = {}
    for prop in expr.properties:
        obj[prop["key"]] = self.evaluate_expr(prop["value"], env)
    return obj
