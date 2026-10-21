from mapple.nodes import MappleError


def Unary(self, expr, env):
    right = self.evaluate_expr(expr.right, env)
    if expr.operator == "-":
        if not isinstance(right, (int, float)):
            raise MappleError(
                expr,
                f"Unary '-' operator can only be applied to numbers. Got: {type(right).__name__}",
            )
        return -right
    if expr.operator == "!":
        return not right
    if expr.operator == "#":
        if isinstance(right, (list, str, dict)) or hasattr(right, "__len__"):
            return len(right)
        raise MappleError(
            expr, f"Unary '#' cannot be applied to {type(right).__name__}"
        )
    raise MappleError(expr, f"Unknown unary operator: {expr.operator}")
