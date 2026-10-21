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
from .parser import Parser
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
    parser: Parser
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
        self.parser = Parser(source, file_path)
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
            except ImportError as E:
                candidate = handlers_dir / f"{mod_name}.py"
                if not candidate.is_file():
                    raise ImportError(
                        f"Cannot load {kind} handler module {mod_name!r} "
                        f"(expected {candidate})"
                    ) from E
                spec = importlib.util.spec_from_file_location(full_name, candidate)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load {candidate}") from E
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
        statements = self.parser.parse_block()
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
