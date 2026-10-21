from mapple.classes.controlFlow import ControlFlow
from mapple.mappleenv import Environment


def With(self, stmt, env):
    nenv = Environment(env)
    expression_val = self.evaluate_expr(stmt.expr, env)
    if getattr(expression_val, "__enter__", None):
        var = expression_val.__enter__()
    elif isinstance(expression_val, dict) and "__enter__" in expression_val:
        var = expression_val["__enter__"]()
    else:
        var = expression_val

    nenv.define(stmt.alias, var)
    returnedVal = None
    try:
        result = self.execute_block(stmt.body, nenv)
        if isinstance(result, ControlFlow):
            returnedVal = result
    except Exception as e:
        handled = False
        if getattr(expression_val, "__exit__", None):
            handled = (
                expression_val.__exit__(  # pyright: ignore[reportAttributeAccessIssue]
                    type(e), e, e.__traceback__
                )
            )
        elif isinstance(expression_val, dict) and "__exit__" in expression_val:
            handled = expression_val["__exit__"](type(e), e, e.__traceback__)

        if not handled:
            raise
    else:
        if getattr(expression_val, "__exit__", None):
            expression_val.__exit__(  # pyright: ignore[reportAttributeAccessIssue]
                None, None, None
            )
        elif isinstance(expression_val, dict) and "__exit__" in expression_val:
            expression_val["__exit__"](None, None, None)
    return returnedVal
