from mapple.classes.mappleError import MappleError
from mapple.mappleclass import MappleClass
from mapple.mappleenv import Environment


def using(self, stmt, env):
    # Helper to import members from a dict/Environment/module into env
    def import_members(value):
        if isinstance(value, MappleClass):
            # Import public static members only
            for key, val in value.get_public_static_members().items():
                env.define(key, val)
        elif isinstance(value, dict) and "__DefiningClass" in value:
            # MappleScript instance: import public instance members
            cls = value["__DefiningClass"]
            for key, val in cls.get_public_instance_members(value).items():
                env.define(key, val)
        elif isinstance(value, Environment):
            for key, var_obj in value.values.items():
                # Environment has no private concept; import everything
                env.define(key, var_obj.value, var_obj.const, var_obj.type_annotation)
        elif isinstance(value, dict):
            # Plain dict – import all keys (no privacy)
            for key, val in value.items():
                env.define(key, val)
        elif hasattr(value, "__dict__"):
            # Python object – skip names starting with '_' (by convention)
            for key, val in value.__dict__.items():
                if not key.startswith("_"):
                    env.define(key, val)
        else:
            raise MappleError(
                stmt,
                f"Cannot 'use' value of type {type(value).__name__}. "
                "Expected a namespace, dict, class, instance, or Python object.",
            )

    if isinstance(stmt.name, list):
        # List of string paths: resolve each and import members
        for path_str in stmt.name:
            parts = path_str.split(".")
            current = env
            for part in parts:
                if isinstance(current, Environment):
                    var_obj = current.get(part, stmt)
                    current = var_obj.value
                elif isinstance(current, dict):
                    current = current.get(part)
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    raise MappleError(
                        stmt,
                        f"Cannot resolve part '{part}' in path '{path_str}'.",
                    )
                if current is None:
                    raise MappleError(
                        stmt,
                        f"Name '{path_str}' part '{part}' not found.",
                    )
            import_members(current)
    else:
        # Single expression: evaluate it, then import members from the result
        value = self.evaluate_expr(stmt.name, env)
        import_members(value)
