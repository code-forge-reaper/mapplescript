from mapple.classes.returnFlow import ReturnFlow


def Return(self, stmt, env):
    if not stmt.expression:
        return ReturnFlow(None)
    value = self.evaluate_expr(stmt.expression, env)
    return ReturnFlow(value)
