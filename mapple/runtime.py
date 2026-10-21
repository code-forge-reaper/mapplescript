#!/usr/bin/env python
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false

import sys
import pathlib

from typing import Any
import uuid
from collections.abc import Iterable, Callable, Sequence, Mapping
import copy
import tomllib
import importlib
import importlib.util

from .mappleclass import bind_parameters
from .mappleenv import FuncWrapp
from .typechecker import CUSTOM_TYPES
from .typechecker import check_type
from .tokenizer import Tokenizer
from .mappleenv import Environment
from .mappleclass import MappleClass
from .helpers import Proxy, dprint
from .nodes import (
    ArrayAccess,
    ArrayLiteral,
    AssignmentExpr,
    BreakFlow,
    ContinueFlow,
    ControlFlow,
    Identifier,
    Literal,
    MappleError,
    MethodDefinition,
    PropertyAccess,
    PropertyDefinition,
    ReturnFlow,
)


__no_variable_set__ = object()


class Interpreter:
    source: str
    file: pathlib.Path
    tk: Tokenizer
    globals: Environment
    modules_loaded: dict[str, Any]  # pyright: ignore[reportExplicitAny]
    current_env: Environment | None
    current_class_stack: list[Any]  # pyright: ignore[reportExplicitAny]
    callStack: list[Any]  # pyright: ignore[reportExplicitAny]
    errorStack: list[Any]  # pyright: ignore[reportExplicitAny]
    _stmt_handlers: dict[str, Callable]  # pyright: ignore[reportMissingTypeArgument]
    _expr_handlers: dict[str, Callable]  # pyright: ignore[reportMissingTypeArgument]

    def __init__(self, source: str, file_path: str | pathlib.Path):
        self.source = source
        c = pathlib.Path(file_path)
        self.file = c.expanduser().resolve()
        # self.file = os.path.abspath(file_path)
        self.tk = Tokenizer(source, file_path)
        self.globals = Environment()

        self.modules_loaded = {}
        self.current_env = None

        self.globals.define("__SCRIPT_PATH__", self.file.parent)
        self.globals.define("__SCRIPT_NAME__", file_path)
        self.globals.define("__IS_MAIN__", True)
        self.current_class_stack = []
        self.callStack = []
        self.errorStack = []

        # ------------------------------------------------------------------
        # Extensibility registries (TOML-driven under mapple/*_handlers/)
        # ------------------------------------------------------------------
        # To add a new expression type:
        #   1. Add the AST node in nodes.py
        #   2. Implement a handler in mapple/expr_handlers/<mod>.py
        #      signature: def HandlerName(self, expr, env): ...
        #   3. Register it in mapple/expr_handlers.toml:
        #        [mod]
        #        AstNodeType = "HandlerName"
        # Same pattern for statements once stmt_handlers.toml exists.
        self._stmt_handlers = {}
        self._expr_handlers = {}
        self._register_default_handlers()

    def _load_handler_toml(self, kind: str) -> None:
        """Load `mapple/{kind}_handlers.toml` and bind handlers into the registry.

        kind is "expr" or "stmt". Missing files are ignored (stmt does not exist yet).
        """
        package_dir = pathlib.Path(__file__).resolve().parent
        toml_path = package_dir / f"{kind}_handlers.toml"
        handlers_dir = package_dir / f"{kind}_handlers"
        registry = self._expr_handlers if kind == "expr" else self._stmt_handlers

        if not toml_path.is_file():
            return

        with open(toml_path, "rb") as f:
            info = tomllib.load(f)

        for mod_name, bindings in info.items():
            full_name = f"mapple.{kind}_handlers.{mod_name}"
            try:
                mod = importlib.import_module(full_name)
            except ImportError:
                candidate = handlers_dir / f"{mod_name}.py"
                if not candidate.is_file():
                    raise ImportError(
                        f"Cannot load {kind} handler module {mod_name!r} "
                        f"(expected {candidate})"
                    )
                spec = importlib.util.spec_from_file_location(full_name, candidate)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load {candidate}")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[full_name] = mod
                spec.loader.exec_module(mod)

            for ast_type, attr_name in bindings.items():
                if not hasattr(mod, attr_name):
                    raise AttributeError(
                        f"{kind}_handlers/{mod_name}.py has no attribute {attr_name!r} "
                        f"(needed for AST type {ast_type!r})"
                    )
                registry[ast_type] = getattr(mod, attr_name)

    def _register_default_handlers(self):
        """Populate registries from expr_handlers.toml / stmt_handlers.toml."""
        self._load_handler_toml("expr")
        self._load_handler_toml("stmt")  # no-op until stmt_handlers.toml exists

    def _create_callable(
        self, parameters, body, env, name=None, node=None, context_name=None
    ):
        """
        Shared factory for both named functions (FuncDecl) and lambdas (LambdaDecl).
        A lambda is simply an unnamed / uuid-named function.

        - Captures the current class context (if any) so nested lambdas can still
          touch private members of the enclosing class.
        - Uses the common bind_parameters helper.
        - Attaches __mapple_ast__ so dynamic method binding continues to work.
        """
        captured_class = (
            self.current_class_stack[-1] if self.current_class_stack else None
        )
        display_name = name or "lambda"
        ctx = context_name or display_name

        def func_wrapper(*args, **kwargs):
            pushed = False
            if captured_class is not None:
                self.current_class_stack.append(captured_class)
                pushed = True
            try:
                func_env = Environment(env)
                bound = bind_parameters(
                    parameters,
                    args,
                    kwargs,
                    self,
                    env,
                    context_name=ctx,
                    token=node,
                )
                for pname, pval in bound.items():
                    func_env.define(pname, pval)
                result = self.execute_block(body, func_env)
                if isinstance(result, ReturnFlow):
                    return result.value
                return None
            finally:
                if pushed and self.current_class_stack:
                    self.current_class_stack.pop()

        wrapper = FuncWrapp(
            func_wrapper,
            (node.__repr__ if node else None),
            (node.__str__ if node else None),
            node,
            self,
            name=display_name,
        )
        wrapper.__name__ = name if name is not None else str(uuid.uuid4())
        if node is not None:
            wrapper.__mapple_ast__ = node  # pyright: ignore
        if captured_class is not None:
            wrapper.__DefiningClass = captured_class  # pyright: ignore
        return wrapper

    def _check_private_access(self, obj, name, expr):
        """Raise MappleError if `name` is a private member of `obj` and access is not from inside its class."""
        if not isinstance(obj, dict) or "__DefiningClass" not in obj:
            return  # not a MappleScript instance
        cls = obj["__DefiningClass"]
        if name in cls._private_properties or name in cls._private_methods:
            # allowed only if the current class (top of stack) is exactly this class
            if not self.current_class_stack or self.current_class_stack[-1] is not cls:
                raise MappleError(
                    expr,
                    f"Private member '{name}' cannot be accessed outside its class",
                )

    # --- Evaluation / Execution ---
    def interpret(self):
        statements = self.tk.parse_block()
        try:
            self.execute_block(statements, self.globals)
        except BaseException as err:
            # Ensure deferred statements still execute
            self.globals.execute_deferred(self)
            if self.errorStack:
                print("\n".join(reversed(self.errorStack)), file=sys.stderr)
            if isinstance(err, MappleError):
                print(f"{err.message}", file=sys.stderr)
            else:
                print(
                    f"{err.__class__.__name__}: {err}"
                )  # trying to print the name and what caused it
            sys.exit(1)

    def execute_block(self, statements, env):
        previous_env = self.current_env
        self.current_env = env
        try:
            for stmt in statements:
                result = self.execute_stmt(stmt, env)
                if isinstance(result, ControlFlow):
                    return result
            return None
        finally:
            # Execute deferred statements in order
            env.execute_deferred(self)
            self.current_env = previous_env

    def get_current_context(self):
        return self.current_env

    def execute_stmt(self, stmt, env):
        dprint("stmt: ", stmt)

        # Prefer registered handler when present (makes new features easy to plug in)
        handler = self._stmt_handlers.get(stmt.type)
        if handler is not None:
            return handler(self, stmt, env)

        if stmt.type in ["VarDecl", "ConstDecl"]:
            value = self.evaluate_expr(stmt.initializer, env)
            if stmt.type_annotation:
                check_type(stmt.type_annotation, value, stmt)
            env.define(stmt.name, value, stmt.type == "ConstDecl", stmt.type_annotation)

        elif stmt.type == "ExportStmt":
            # Execute the inner statement first
            self.execute_stmt(stmt.expr, env)

            # Ensure exports dictionary exists (it should in modules, but create if missing)
            if not env.has("exports"):
                env.define("exports", {})
            exports_dict = env.get("exports").value

            inner = stmt.expr
            if inner.type in ("VarDecl", "ConstDecl", "FuncDecl", "ClassDefinition"):
                # For declarations, export the declared name
                name = inner.name
                if name in exports_dict:
                    raise MappleError(stmt, f"cannot re-export: {name}")
                value = env.get(name).value
                exports_dict[name] = value

            elif inner.type == "ExpressionStmt":
                expr = inner.expression
                if expr.type == "ObjectLiteral":
                    # export { a, b, c: d } → evaluate each property
                    for prop in expr.properties:
                        key = prop["key"]
                        val_expr = prop["value"]
                        if key in exports_dict:
                            raise MappleError(stmt, f"cannot re-export: {name}")
                        if val_expr.type == "Identifier":
                            val = env.get(val_expr.name).value
                        else:
                            val = self.evaluate_expr(val_expr, env)
                        exports_dict[key] = val
                elif expr.type == "Identifier":
                    # export a → export the variable 'a'
                    name = expr.name
                    if name in exports_dict:
                        raise MappleError(stmt, f"cannot re-export: {name}")
                    val = env.get(name).value
                    exports_dict[name] = val
                else:
                    raise MappleError(
                        stmt, f"Cannot export expression of type {expr.type}"
                    )

            else:
                raise MappleError(stmt, f"Cannot export statement of type {inner.type}")
        elif stmt.type == "DeferStmt":
            for s in stmt.body:
                env.add_deferred(s)

        elif stmt.type == "ExpressionStmt":
            self.evaluate_expr(stmt.expression, env)

        elif stmt.type == "BreakStmt":
            return BreakFlow()

        elif stmt.type == "ContinueStmt":
            return ContinueFlow()

        elif stmt.type == "TryStmt":
            try:
                result = self.execute_block(stmt.try_block, env)
                if isinstance(result, ControlFlow) and not isinstance(
                    result, ReturnFlow
                ):
                    return result
            except Exception as e:  # Catch all other Python exceptions
                catch_env = Environment(env)
                # If e is a MappleError, use it directly. Otherwise, wrap it.
                catch_env.define(stmt.error_var, e, True)
                result = self.execute_block(stmt.catch_block, catch_env)
                if isinstance(result, ControlFlow):
                    return result
        elif stmt.type == "WithStmt":
            nenv = Environment(env)
            expression_val = self.evaluate_expr(stmt.expr, env)
            if getattr(expression_val, "__enter__", None):
                var = expression_val.__enter__()
            elif isinstance(expression_val, dict) and "__enter__" in expression_val:
                var = expression_val["__enter__"]()
            else:
                var = expression_val

            nenv.define(stmt.alias, var)
            returnedVal = None
            try:
                result = self.execute_block(stmt.body, nenv)
                if isinstance(result, ControlFlow):
                    returnedVal = result
            except Exception as e:
                handled = False
                if getattr(expression_val, "__exit__", None):
                    handled = expression_val.__exit__(  # pyright: ignore[reportAttributeAccessIssue]
                        type(e), e, e.__traceback__
                    )
                elif isinstance(expression_val, dict) and "__exit__" in expression_val:
                    handled = expression_val["__exit__"](type(e), e, e.__traceback__)

                if not handled:
                    raise
            else:
                if getattr(expression_val, "__exit__", None):
                    expression_val.__exit__(  # pyright: ignore[reportAttributeAccessIssue]
                        None, None, None
                    )
                elif isinstance(expression_val, dict) and "__exit__" in expression_val:
                    expression_val["__exit__"](None, None, None)
            return returnedVal

        elif stmt.type == "IfStmt":
            condition = self.evaluate_expr(stmt.condition, env)
            if condition:
                result = self.execute_block(stmt.then_block, Environment(env))
                if isinstance(result, ControlFlow):
                    return result
            elif stmt.else_if:
                matched = False
                for elseif_block in stmt.else_if:
                    elseif_condition = self.evaluate_expr(
                        elseif_block["condition"], env
                    )
                    if elseif_condition:
                        result = self.execute_block(
                            elseif_block["body"], Environment(env)
                        )
                        if isinstance(result, ControlFlow):
                            return result
                        matched = True
                        break
                if not matched and stmt.else_block:
                    result = self.execute_block(stmt.else_block, Environment(env))
                    if isinstance(result, ControlFlow):
                        return result
            elif stmt.else_block:
                result = self.execute_block(stmt.else_block, Environment(env))
                if isinstance(result, ControlFlow):
                    return result

        elif stmt.type == "ObjectDecl":
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
        elif stmt.type == "WhileStmt":
            while self.evaluate_expr(stmt.condition, env):
                result = self.execute_block(stmt.body, Environment(env))
                if isinstance(result, BreakFlow):
                    break
                if isinstance(result, ReturnFlow):
                    return result
                if isinstance(result, ContinueFlow):
                    continue
        elif stmt.type == "UntilStmt":
            while not self.evaluate_expr(stmt.condition, env):
                result = self.execute_block(stmt.body, Environment(env))
                if isinstance(result, BreakFlow):
                    break
                if isinstance(result, ReturnFlow):
                    return result
                if isinstance(result, ContinueFlow):
                    continue
        elif stmt.type == "ForEachStmt":
            list_val = self.evaluate_expr(stmt.list, env)
            if not isinstance(list_val, (list, dict)) and not hasattr(
                list_val, "__iter__"
            ):
                raise MappleError(
                    stmt,
                    f"Cannot iterate over non-array type for forEach loop. Got: {type(list_val).__name__}",
                )
            for item in list_val:
                loop_env = Environment(env)
                loop_env.define(stmt.variable, item)
                result = self.execute_block(stmt.body, loop_env)
                if isinstance(result, BreakFlow):
                    break
                if isinstance(result, ReturnFlow):
                    return result
                if isinstance(result, ContinueFlow):
                    continue
        elif stmt.type == "ForStmt":
            start = self.evaluate_expr(stmt.start, env)
            end = self.evaluate_expr(stmt.end, env)
            step = self.evaluate_expr(stmt.step, env) if stmt.step else 1

            if not all(isinstance(val, (int, float)) for val in [start, end, step]):
                raise MappleError(
                    stmt,
                    f"For loop bounds and step must be numbers. Got start: {type(start).__name__}, end: {type(end).__name__}, step: {type(step).__name__}",
                )

            # Python's range handles step correctly. For float steps, manual loop.
            # Assuming integer steps for now, as floats can lead to precision issues.
            # If MappleScript intends float steps, this will need adjustment.
            if isinstance(step, float):
                current_val = start
                while (step > 0 and current_val <= end) or (
                    step < 0 and current_val >= end
                ):
                    loop_env = Environment(env)
                    loop_env.define(stmt.variable, current_val)
                    result = self.execute_block(stmt.body, loop_env)
                    if isinstance(result, BreakFlow):
                        break
                    if isinstance(result, ReturnFlow):
                        return result
                    if isinstance(result, ContinueFlow):
                        current_val += step
                        continue
                    current_val += step
            else:  # Integer step
                for i in range(start, end + (1 if step > 0 else -1), step):
                    loop_env = Environment(env)
                    loop_env.define(stmt.variable, i)
                    result = self.execute_block(stmt.body, loop_env)
                    if isinstance(result, BreakFlow):
                        break
                    if isinstance(result, ReturnFlow):
                        return result
                    if isinstance(result, ContinueFlow):
                        continue
        elif stmt.type == "ScopeStmt":
            n_env = Environment(env)
            n_env.localsOnly = True
            result = self.execute_block(stmt.body, n_env)
            env.define(stmt.name, n_env)
            if isinstance(result, ControlFlow):
                return result

        elif stmt.type == "SwitchStmt":
            value = self.evaluate_expr(stmt.expression, env)
            matched = False
            default_case_body = None
            for case in stmt.cases:
                if case.case_expr is None:  # This is the default case
                    default_case_body = case.body
                else:
                    case_val = self.evaluate_expr(case.case_expr, env)
                    if value == case_val:
                        result = self.execute_block(case.body, Environment(env))
                        if isinstance(result, ControlFlow):
                            return result
                        matched = True
                        break  # Exit switch after first match

            if not matched and default_case_body and not stmt.strict:
                result = self.execute_block(default_case_body, Environment(env))
                if isinstance(result, ControlFlow):
                    return result

            if stmt.strict and not matched:
                raise MappleError(
                    stmt, f"Switch statement did not match any case for value: {value}"
                )

        elif stmt.type == "ReturnStmt":
            if not stmt.expression:
                return ReturnFlow(None)
            value = self.evaluate_expr(stmt.expression, env)
            return ReturnFlow(value)
        elif stmt.type == "LocalFuncDecl":
            _env = Environment(env)
            _env.localsOnly = True
            self.execute_stmt(stmt.fn, _env)
            env.define(
                stmt.fn.name, _env.get(stmt.fn.name).value, _env.get(stmt.fn.name).const
            )
        elif stmt.type == "FuncDecl":
            # Named function – same machinery as a lambda, just with a name
            # and stored in the environment.
            func_wrapper = self._create_callable(
                stmt.parameters,
                stmt.body,
                env,
                name=stmt.name,
                node=stmt,
                context_name=f"function '{stmt.name}'",
            )
            env.define(stmt.name, func_wrapper)

        elif stmt.type == "ClassDefinition":
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
        elif stmt.type == "AssertStmt":
            e = self.evaluate_expr(stmt.expression, env)
            if not e:
                raise MappleError(stmt, f"{stmt.message}")
        elif stmt.type == "UsingStmt":
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
                        env.define(
                            key, var_obj.value, var_obj.const, var_obj.type_annotation
                        )
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
        else:
            raise MappleError(stmt, f"Unknown statement type: {stmt.type}")

    # --- NEW HELPER: Resolves the base object and final key/index for assignment ---
    def resolve_assignment_target(self, target_expr, env):
        if isinstance(target_expr, Identifier):
            # For simple identifiers, the base is the environment and the key is the identifier name
            return {"base": env, "final_key": target_expr.name}
        if isinstance(target_expr, ArrayAccess):
            # Recursively evaluate the object part to get the actual array/object
            base_object = self.evaluate_expr(target_expr.object, env)
            index = self.evaluate_expr(target_expr.index, env)

            if base_object is None:
                raise MappleError(target_expr, "Cannot assign to index of None value.")
            if not isinstance(base_object, (list, dict)) and not hasattr(
                base_object, "__setitem__"
            ):  # Python lists/dicts for arrays/objects
                # print(dir(base_object))
                raise MappleError(
                    target_expr,
                    f"Cannot assign to index of non-list/dict: {type(base_object).__name__}",
                )
            if not isinstance(index, (int, str)):
                raise MappleError(
                    target_expr,
                    f"List/dict index must be a number or string for assignment. Got: {type(index).__name__}",
                )
            return {"base": base_object, "final_key": index}
        if isinstance(target_expr, PropertyAccess):
            # Recursively evaluate the object part to get the actual object
            base_object = self.evaluate_expr(target_expr.object, env)
            key = target_expr.property  # Property name is a string

            if base_object is None:
                raise MappleError(
                    target_expr, f"Cannot assign property '{key}' of None value."
                )

            # Special case: if the base object is an Environment, we assign to it directly
            if isinstance(base_object, Environment):
                return {"base": base_object, "final_key": key}
            # If the base object is a MappleScript instance (a Python dict), assign to its key.
            if isinstance(base_object, dict):
                return {"base": base_object, "final_key": key}
            # For other Python objects, assume it's a regular attribute access.
            return {"base": base_object, "final_key": key}
        raise MappleError(
            target_expr, "Invalid assignment target type: " + target_expr.type
        )

    def get_target_type(self, target, env):
        """Resolve the expected type for an assignment target (Identifier or nested PropertyAccess)."""
        if isinstance(target, Identifier):
            var = env.get(target.name, target)
            return var.type_annotation

        if isinstance(target, PropertyAccess):
            # Recurse to get the type of the parent object
            parent_type = self.get_target_type(target.object, env)
            if not parent_type or parent_type not in CUSTOM_TYPES:
                return None
            custom_def = CUSTOM_TYPES[parent_type]
            prop_def = next(
                (p for p in custom_def.properties if p.name == target.property), None
            )
            return prop_def.type if prop_def else None

        # ArrayAccess or anything else → no static type check for now
        return None

    def evaluate_expr(self, expr, env):
        dprint("expr: ", expr)

        # Prefer registered handler when present (extension point for new expr types)
        handler = self._expr_handlers.get(expr.type)
        if handler is not None:
            return handler(self, expr, env)

        if expr.type == "Literal":
            return expr.value
        if expr.type == "Identifier":
            return env.get(expr.name, expr).value

        raise MappleError(expr, f"Unknown expression type: {expr}")
