from typing import Iterable

from mapple.mappleclass import MappleClass
from mapple.mappleenv import Environment
from mapple.nodes import MappleError
from mapple.typechecker import CUSTOM_TYPES, check_type


def New(self, expr, env):
    # Resolve the fully qualified class name string
    name_parts = expr.class_name.split(".")
    current_resolved_object = env  # Start resolution from current environment

    for i, part in enumerate(name_parts):
        if isinstance(current_resolved_object, Environment):
            # FIX: Get value from var
            var_obj = current_resolved_object.get(part, expr)
            next_resolved_part = var_obj.value
        elif isinstance(current_resolved_object, dict):
            next_resolved_part = current_resolved_object.get(part)
        elif hasattr(current_resolved_object, part):
            next_resolved_part = getattr(current_resolved_object, part)
        else:
            raise MappleError(
                expr,
                f"Cannot resolve part '{part}' in class path '{expr.class_name}'. Previous part was type {type(current_resolved_object).__name__}.",
            )

        if next_resolved_part is None:
            raise MappleError(
                expr, f"Class '{expr.class_name}' part '{part}' not found."
            )

        current_resolved_object = next_resolved_part

    target_class = current_resolved_object
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
            args.append(self.evaluate_expr(arg, env))
    c = None
    if isinstance(target_class, MappleClass):
        c = target_class.instantiate(args, kwargs)
    elif isinstance(target_class, type) and hasattr(
        target_class, "__init__"
    ):  # It's a Python class
        # For Python classes, we instantiate them directly.
        try:
            c = target_class(*args, **kwargs)
        except Exception as e:
            raise MappleError(
                expr,
                f"Error instantiating Python class '{expr.class_name}' (resolved to {target_class}): {e}",
            ) from e
    else:
        raise MappleError(
            expr,
            f"'{expr.class_name}' (resolved to {target_class}) is not a constructible class.",
        )
    if CUSTOM_TYPES.get(expr.class_name):
        check_type(
            expr.class_name,
            c,
            expr,
        )
    return c
