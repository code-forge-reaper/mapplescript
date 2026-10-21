from mapple.nodes import MappleError


def Decorator(self, expr, env):
    # print(expr.__dict__)
    value = self.evaluate_expr(expr.expr, env)
    if not callable(value):
        raise MappleError(expr.expr, "Expected to return a function")
    # print(f"{value = }")
    body = self.evaluate_expr(expr.body, env)

    if not callable(body):
        raise MappleError(expr.body, "Expected to be a function")
    # print(f"{body = }")
    val = value(body)
    # print(f"{val = }")
    return val
