from collections.abc import Iterable

from mapple.mappleclass import MappleClass
from mapple.mappleenv import Environment
from mapple.nodes import MappleError


def Call(self, expr, env):
    obj = self.evaluate_expr(expr.object, env)
    self._check_private_access(obj, expr.method, expr)
    if obj is None:
        raise MappleError(expr, f"Cannot call method '{expr.method}' on None.")

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

    # Handle MappleClass static methods
    if isinstance(obj, MappleClass):
        static_method = obj.static_members.get(expr.method)
        if callable(static_method):
            return static_method(*args, **kwargs)
        raise MappleError(
            expr,
            f"Static method '{expr.method}' not found or is not a function on class '{obj.name}'.",
        )

    fn = None
    # If obj is a MappleScript instance (represented as a Python dictionary)
    if isinstance(obj, dict) and expr.method in obj:
        fn = obj[expr.method]
    # If obj is an Environment (e.g., 'self' within a MappleScript method)
    elif isinstance(obj, Environment):
        # FIX: Get value from var
        fn = obj.get(expr.method, expr).value
    # For regular Python objects exposed to MappleScript
    else:
        fn = getattr(obj, expr.method, None)

    if not callable(fn):
        raise MappleError(
            expr, f"{expr.method} is not a function or method on this object"
        )

    # Push class context if the method has a defining clas attribute (MappleScript bound method)
    if isinstance(obj, dict) and "__DefiningClass" in obj:
        # Push the defining class before calling the method
        self.current_class_stack.append(obj["__DefiningClass"])
        try:
            result = fn(*args, **kwargs)
        finally:
            self.current_class_stack.pop()
        return result
    else:
        try:
            if hasattr(fn, "__DefiningClass"):
                self.current_class_stack.append(
                    fn.__DefiningClass
                )  # pyright: ignore[reportAny, reportFunctionMemberAccess]
            result = fn(*args, **kwargs)
        finally:
            if hasattr(fn, "__DefiningClass"):
                self.current_class_stack.pop()
        return result
