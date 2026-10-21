from mapple.classes.mappleError import MappleError
from mapple.classes.methodDefinition import MethodDefinition
from mapple.classes.propertyDefinition import PropertyDefinition
from mapple.mappleclass import MappleClass


def Object(self, stmt, env):
    temp_class = MappleClass(f"__anon_{stmt.name}", None, self, env)

    for member in stmt.body:
        if member.type == "FuncDecl":
            if member.name == "init":
                method_def = MethodDefinition(
                    member.name,
                    member.parameters,
                    member.body,
                    False,
                    True,
                    False,
                    member.file,
                    member.line,
                    member.column,
                )
                temp_class.constructor_def = method_def

            else:
                method_def = MethodDefinition(
                    member.name,
                    member.parameters,
                    member.body,
                    False,
                    False,
                    False,
                    member.file,
                    member.line,
                    member.column,
                )
                temp_class.instance_methods[member.name] = method_def
        elif member.type == "VarDecl":
            # Treat 'var' as instance properties
            prop_def = PropertyDefinition(
                member.name,
                member.type_annotation,
                member.initializer,
                False,  # is_static
                False,  # is_private
                False,  # is_const
                member.file,
                member.line,
                member.column,
            )
            temp_class.instance_properties[member.name] = prop_def

        elif member.type == "PropertyDefinition":
            # Use member directly or create a new one with forced flags
            prop_def = PropertyDefinition(
                member.name,
                member.type_annotation,
                member.initializer,
                False,  # non‑static
                False,  # non‑private
                getattr(member, "is_const", False),
                member.file,
                member.line,
                member.column,
            )
            temp_class.instance_properties[member.name] = prop_def

        elif member.type == "PropertyHandler":
            # Add getter and setter as methods
            temp_class.instance_methods[member.getter.name] = member.getter
            temp_class.instance_methods[member.setter.name] = member.setter

        else:
            raise MappleError(member, "not supported")

    # 4. Instantiate and assign to the variable name provided
    instance = temp_class.instantiate([])
    env.define(stmt.name, instance)
