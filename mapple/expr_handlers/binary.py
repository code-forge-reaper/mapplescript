from mapple.helpers import dprint, opToName
from mapple.nodes import MappleError


def Binary(self, expr, env):
    dprint("BinOp", expr)
    if expr.operator == "&&":
        f = self.evaluate_expr(expr.left, env)
        if not f:
            return f
        return self.evaluate_expr(expr.right, env)
    if expr.operator == "||":
        f = self.evaluate_expr(expr.left, env)
        if f:
            return f
        return self.evaluate_expr(expr.right, env)
    left = self.evaluate_expr(expr.left, env)
    right = self.evaluate_expr(expr.right, env)

    # Handle operator overloading for custom objects (dicts)
    if isinstance(left, dict):
        op = opToName(expr.operator)
        if op and op in left and callable(left[op]):
            try:
                return left[op](right)
            except Exception as e:
                raise MappleError(
                    expr, f"Error calling overloaded operator '{op}': {e}"
                ) from e
        # If no operator overloading found, fall through to normal operations

    # Normal binary operations
    if expr.operator == "+":
        return left + right
    if expr.operator == "|":
        return left | right
    if expr.operator == "&":
        return left & right
    if expr.operator == "%":
        if isinstance(left, str):
            if isinstance(right, list):
                return left.format(*right)
            if isinstance(right, dict):
                return left.format(**right)
            raise MappleError(
                expr,
                f"'%' formatting requires a list or object on the right, got {type(right).__name__}",
            )
        return left % right
    if expr.operator == "^":
        return left ^ right
    if expr.operator == "-":
        return left - right
    if expr.operator == "*":
        if isinstance(left, (int, float)) and not isinstance(right, (int, float)):
            raise MappleError(
                expr,
                f"If you wanted to repeat '{right}' {left} times, you'd do '\"{right}\" * {left}'",
            )
        return left * right  # pyright: ignore[reportOperatorIssue]
    if expr.operator == "**":
        return left**right
    if expr.operator == "/":
        if right == 0:
            raise MappleError(expr, "Division by zero is not allowed.")
        return left / right
    if expr.operator == "==":
        return left == right
    if expr.operator == "!=":
        return left != right
    if expr.operator == "<":
        return left < right
    if expr.operator == ">":
        return left > right
    if expr.operator == ">>":
        return left >> right
    if expr.operator == "<<":
        return left << right
    if expr.operator == "<=":
        return left <= right
    if expr.operator == "between":
        if not isinstance(right, (list, tuple)) or len(right) != 2:
            raise MappleError(expr, "'between' requires a range [low, high]")
        return right[0] <= left <= right[1]
    if expr.operator == ">=":
        return left >= right
    if expr.operator == "->":
        if not callable(right):
            raise MappleError(expr, "right side of pipe expr must be a function")
        return right(left)
    if expr.operator == "=>":
        if not callable(right):
            raise MappleError(expr, "right side of pipe expr must be a function")
        clone = copy.deepcopy(left)
        if isinstance(clone, dict):
            for k, v in clone.items():
                clone[k] = right(v, k)
        elif isinstance(clone, list):
            for i, v in enumerate(clone):
                clone[i] = right(v, i)
        else:
            raise MappleError(expr, "=> only works on arrays or objects")
        return clone
    raise MappleError(expr, f"Unknown binary operator: {expr.operator}")
