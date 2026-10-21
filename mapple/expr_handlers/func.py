from collections.abc import Iterable

from mapple.nodes import MappleError


def Call(self, expr, env):
    # Evaluate the callee expression (Identifier, ArrayAccess, etc.)
    callee = self.evaluate_expr(expr.callee, env)
    name_for_stack = getattr(expr.callee, "name", str(expr.callee))
    self.callStack.append(name_for_stack)
    try:
        if not callable(callee):
            raise MappleError(
                expr,
                f"{name_for_stack} is not a function (got {type(callee).__name__})",
            )
        args = []
        kwargs = {}
        for arg in expr.arguments:
            if arg.type == "ExplodeExpr":
                v = self.evaluate_expr(arg.args, env)
                if isinstance(v, dict):
                    for name in v.keys():
                        kwargs[name] = v[name]
                elif isinstance(v, Iterable) and not isinstance(v, (str, bytes)):
                    args.extend(v)
                else:
                    args.append(v)
            elif arg.type == "NamedArg":
                kwargs[arg.name] = self.evaluate_expr(arg.value, env)
            else:
                v = self.evaluate_expr(arg, env)
                args.append(v)
        return callee(*args, **kwargs)
    except Exception as E:  # pyright: ignore[reportConstantRedefinition]
        self.errorStack.append(
            " " * len(self.callStack)
            + f"- {expr.file}:{expr.line}:{expr.column}: "
            + "Error while executing: "
            + str(name_for_stack)
        )
        raise E
    finally:
        self.callStack.pop()
