from mapple.helpers import Proxy
from mapple.mappleclass import MappleClass
from mapple.mappleenv import Environment
from mapple.nodes import MappleError


def Access(self, expr, env):
    obj = self.evaluate_expr(expr.object, env)
    self._check_private_access(obj, expr.property, expr)

    if obj is None:
        raise MappleError(expr, f"Cannot access property '{expr.property}' of None.")

    # Handle MappleClass static properties
    if isinstance(obj, MappleClass):
        if expr.property in obj.static_members:
            return obj.static_members[expr.property]
        raise MappleError(
            expr,
            f"Static property '{expr.property}' not found on class '{obj.name}'.",
        )
    if isinstance(obj, dict) and expr.property in obj:
        val = obj[expr.property]
        if isinstance(val, Proxy):
            if not val.get:
                raise MappleError(expr, f"Property '{expr.property}' has no getter.")
            cls = obj.get("__DefiningClass")
            if cls:
                try:
                    self.current_class_stack.append(cls)
                    return val.get()
                finally:
                    self.current_class_stack.pop()
            else:
                return val.get()
        return val
    # If obj is a MappleScript instance (represented as a Python dictionary)
    # if isinstance(obj, dict) and expr.property in obj:
    #    return obj[expr.property]
    # If obj is an Environment (e.g., 'self' within a MappleScript method)
    if isinstance(obj, Environment):
        # FIX: Get value from var
        return obj.get(expr.property, expr).value
    # For regular Python objects (e.g., exposed modules, native types)
    if hasattr(obj, expr.property):
        return getattr(obj, expr.property)

    return None
    # raise MappleError(expr, f"Property '{expr.property}' not found on object.")
