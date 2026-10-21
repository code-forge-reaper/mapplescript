from mapple.classes.mappleError import MappleError
from mapple.classes.returnFlow import ReturnFlow
from mapple.mappleclass import MappleClass, bind_parameters
from mapple.mappleenv import Environment


def ClassDef(self, stmt, env):
    class_def = stmt
    super_class = None
    if class_def.superclass_name:
        # Resolve the fully qualified superclass name
        name_parts = class_def.superclass_name.split(".")
        current_resolved_object = env
        for i, part in enumerate(name_parts):
            if isinstance(current_resolved_object, Environment):
                # FIX: Get value from var
                var_obj = current_resolved_object.get(part, class_def)
                next_resolved_part = var_obj.value
            elif isinstance(current_resolved_object, dict):
                next_resolved_part = current_resolved_object.get(part)
            elif hasattr(current_resolved_object, part):
                next_resolved_part = getattr(current_resolved_object, part)
            else:
                raise MappleError(
                    class_def,
                    f"Cannot resolve part '{part}' in superclass path '{class_def.superclass_name}'.",
                )

            if next_resolved_part is None:
                raise MappleError(
                    class_def,
                    f"Superclass '{class_def.superclass_name}' part '{part}' not found.",
                )

            current_resolved_object = next_resolved_part

        super_class = current_resolved_object

        # Allow MappleClass or Python type/class as superclass
        if not isinstance(super_class, (MappleClass, type)):
            raise MappleError(
                class_def,
                f"Superclass '{class_def.superclass_name}' resolved to type {type(super_class).__name__}, which is not a class.",
            )

    # Pass the resolved super_class to MappleClass
    mapple_class = MappleClass(class_def.name, super_class, self, env)

    # Populate static members, instance properties/methods
    for member in class_def.body:
        if member.type == "PropertyDefinition":
            if member.is_private:
                mapple_class._private_properties.add(member.name)
            if getattr(member, "is_const", False):
                mapple_class._const_properties.add(member.name)
            if member.is_static:
                prop_value = None
                if member.initializer:
                    prop_value = self.evaluate_expr(member.initializer, env)
                mapple_class.static_members[member.name] = prop_value
                if getattr(member, "is_const", False):
                    mapple_class._static_const.add(member.name)
            else:
                mapple_class.instance_properties[member.name] = member
        elif member.type == "PropertyHandler":
            mapple_class.instance_properties[member.name] = member

        elif member.type == "MethodDefinition":
            if member.is_private:
                mapple_class._private_methods.add(member.name)
            if member.is_constructor:
                mapple_class.constructor_def = member
            elif member.is_static:
                # Wrap static methods using shared bind helper
                def static_method_wrapper(*args, _member=member, **kwargs):
                    method_env = Environment(env)
                    method_env.define("self", mapple_class.static_members)
                    bound = bind_parameters(
                        _member.parameters,
                        args,
                        kwargs,
                        self,
                        env,
                        context_name=f"static method '{_member.name}'",
                        token=_member,
                    )
                    for pname, pval in bound.items():
                        method_env.define(pname, pval)
                    result = self.execute_block(_member.body, method_env)
                    if isinstance(result, ReturnFlow):
                        return result.value
                    return None

                mapple_class.static_members[member.name] = static_method_wrapper
            else:
                mapple_class.instance_methods[member.name] = member
        else:
            raise MappleError(member, f"not supported: {member}")

    env.define(class_def.name, mapple_class)
