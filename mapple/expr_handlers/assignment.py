from collections.abc import Mapping, Sequence
from typing import Callable

from mapple.helpers import Proxy
from mapple.mappleenv import Environment
from mapple.nodes import (
    ArrayLiteral,
    AssignmentExpr,
    Literal,
    MappleError,
    MethodDefinition,
)
from mapple.typechecker import check_type


def Assign(self, expr, env):
    target = expr.target
    op = expr.operator

    # Resolve where we are assigning to
    resolved = self.resolve_assignment_target(target, env)
    base = resolved["base"]
    final_key = resolved["final_key"]

    assigned_value = self.evaluate_expr(expr.value, env)

    # === Compound assignment handling ===
    if op != "=":
        if isinstance(base, Environment):
            current_value = base.get(
                final_key, target
            ).value  # pyright: ignore[reportArgumentType]
        elif isinstance(base, Mapping):
            # dict and other mappings (supports str/int keys)
            try:
                current_value = base[final_key]
            except KeyError as e:
                raise MappleError(
                    target,
                    f"Cannot read key '{final_key}' for compound assignment: {e}",
                ) from e
        elif isinstance(base, Sequence) or hasattr(base, "__getitem__"):
            # lists, tuples, strings, custom indexable objects
            try:
                current_value = base[
                    final_key
                ]  # pyright: ignore[reportCallIssue, reportArgumentType, reportIndexIssue]
            except (IndexError, KeyError, TypeError) as e:
                raise MappleError(
                    target,
                    f"Cannot read index/key '{final_key}' for compound assignment: {e}",
                ) from e
        else:
            current_value = getattr(
                base, final_key, None
            )  # pyright: ignore[reportCallIssue, reportArgumentType]
        if isinstance(current_value, Proxy):
            if not current_value.get:
                raise MappleError(target, f"Property '{final_key}' has no getter.")
            current_value = current_value.get()

        if op == "+=":
            final_value_to_assign = current_value + assigned_value
        elif op == "-=":
            final_value_to_assign = current_value - assigned_value
        elif op == "*=":
            if isinstance(current_value, (int, float)) and not isinstance(
                assigned_value, (int, float)
            ):
                raise MappleError(
                    expr,
                    f"If you wanted to repeat '{assigned_value}' {current_value} times, "
                    f"you'd do '\"{assigned_value}\" * {current_value}'",
                )
            final_value_to_assign = (
                current_value * assigned_value
            )  # pyright: ignore[reportOperatorIssue]
        elif op == "/=":
            if assigned_value == 0:
                raise MappleError(expr, "Division by zero in compound assignment.")
            final_value_to_assign = current_value / assigned_value
        elif op == "%=":
            final_value_to_assign = current_value % assigned_value
        else:
            raise MappleError(expr, f"Unknown compound assignment operator: {op}")
    else:
        final_value_to_assign = assigned_value

    # === Perform the actual assignment + type checking ===
    if isinstance(target, ArrayLiteral):  # destructuring
        source_array = final_value_to_assign
        if not isinstance(source_array, list):
            raise MappleError(
                target,
                f"Cannot destructure non-list value. Expected list, got {type(source_array).__name__}.",
            )
        for i, target_element in enumerate(target.elements):
            source_value = source_array[i] if i < len(source_array) else None
            temp_assignment = AssignmentExpr(
                target_element,
                Literal(source_value, expr.file, expr.line, expr.column),
                "=",
                expr.file,
                expr.line,
                expr.column,
            )
            self.evaluate_expr(temp_assignment, env)

    else:  # normal / property / nested assignment
        if isinstance(base, Environment):
            var = base.get(final_key, target)  # pyright: ignore[reportArgumentType]
            if var.type_annotation:
                check_type(var.type_annotation, final_value_to_assign, target)
            base.assign(final_key, final_value_to_assign, target)

        elif isinstance(base, dict):
            # Enforce const properties on Mapple instances
            const_set = base.get("__const__")
            if const_set and final_key in const_set:
                raise MappleError(
                    target,
                    f"Cannot re-assign constant property '{final_key}'",
                )
            # Resolve expected type for (possibly nested) property using root variable's type
            if final_key in base and isinstance(base[final_key], Proxy):
                proxy = base[final_key]
                if (
                    not proxy.set  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                ):
                    raise MappleError(target, f"Property '{final_key}' has no setter.")
                cls = base.get("__DefiningClass")
                if cls:
                    try:
                        self.current_class_stack.append(cls)
                        proxy.set(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                            final_value_to_assign
                        )
                    finally:
                        self.current_class_stack.pop()
                else:
                    proxy.set(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                        final_value_to_assign
                    )
            elif "__DefiningClass" in base and isinstance(assigned_value, Callable):
                # === Dynamic method binding ===
                # Makes it easy to do: instance.foo = def() print(self.name) end
                # We prefer the original AST (LambdaDecl) when available so we
                # can reconstruct a proper MethodDefinition that receives `self`.
                # Extension point: if you add new callable AST nodes, just attach
                # .__mapple_ast__ on the wrapper (see LambdaDecl evaluation).
                ast_node = getattr(assigned_value, "__mapple_ast__", None)
                if (
                    ast_node is not None
                    and hasattr(ast_node, "parameters")
                    and hasattr(ast_node, "body")
                ):
                    meth = MethodDefinition(
                        final_key,
                        ast_node.parameters,
                        ast_node.body,
                        False,  # is_static
                        False,  # is_constructor
                        False,  # is_private
                        expr.file,
                        expr.line,
                        expr.column,
                    )
                    bound = base["__DefiningClass"]._create_method(
                        meth, base
                    )  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                    base[final_key] = bound
                elif hasattr(expr.value, "parameters") and hasattr(expr.value, "body"):
                    # Fallback: RHS was still the raw AST (should not normally happen)
                    meth = MethodDefinition(
                        final_key,
                        expr.value.parameters,
                        expr.value.body,
                        False,
                        False,
                        False,
                        expr.file,
                        expr.line,
                        expr.column,
                    )
                    bound = base[
                        "__DefiningClass"
                    ]._create_method(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                        meth, base
                    )
                    base[final_key] = bound
                else:
                    # Plain Python callable or already-bound function – store as-is
                    base[final_key] = final_value_to_assign

            else:
                expected_type = self.get_target_type(target, env)
                if expected_type:
                    check_type(expected_type, final_value_to_assign, target)
                base[final_key] = final_value_to_assign

        else:
            # Python object
            try:
                setattr(
                    base, final_key, final_value_to_assign
                )  # pyright: ignore[reportArgumentType]
            except (AttributeError, TypeError) as E:
                if isinstance(base, (dict, list)) or hasattr(base, "__setitem__"):
                    base[  # pyright: ignore[reportCallIssue, reportArgumentType, reportIndexIssue]
                        final_key
                    ] = final_value_to_assign
                else:
                    raise MappleError(
                        target,
                        f"Cannot assign to property '{final_key}' of object of type {type(base).__name__}.",
                    ) from E

    return final_value_to_assign
