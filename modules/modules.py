import builtins
import importlib
import importlib.util
import json
import math
import pathlib
import sys
import tomllib
from typing import Any, Iterable

from mapple.conf import FILE_EXTENSION, LIBS_PATH
from mapple.mappleenv import Environment
from mapple.nodes import MappleError
from mapple.runtime import Interpreter
from mapple.typechecker import BUILTIN_VAR_TYPES


# ─────────────────────────────────────────────────────────────────────────────
# Module loading
# ─────────────────────────────────────────────────────────────────────────────


def _dedup(paths: Iterable[pathlib.Path]) -> list[pathlib.Path]:
    """Resolve paths and drop duplicates while preserving order."""
    seen: set[pathlib.Path] = set()
    out: list[pathlib.Path] = []
    for p in paths:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            out.append(resolved)
    return out


def _mapple_candidates(
    raw: pathlib.Path, interp_dir: pathlib.Path
) -> list[pathlib.Path]:
    return _dedup(
        [
            raw,
            interp_dir / raw,
            pathlib.Path.cwd() / raw,
            LIBS_PATH / raw,
        ]
    )


def _load_python_module(
    py_path: str,
    interpreter: Interpreter,
    search_dirs: Iterable[pathlib.Path] = (),
):
    """Load a Python module either from the import system or from a file path."""
    cached = interpreter.modules_loaded.get(py_path)
    if cached is not None:
        return cached

    # Try the normal import system first.
    try:
        mod = importlib.import_module(py_path)
        interpreter.modules_loaded[py_path] = mod
        return mod
    except ImportError:
        pass

    # Fall back to loading from the given search directories.
    rel = pathlib.Path(*py_path.split("."))
    for d in search_dirs:
        for candidate in (
            (pathlib.Path(d) / rel).with_suffix(".py"),
            pathlib.Path(d) / rel / "__init__.py",
        ):
            candidate = candidate.resolve()
            if not candidate.is_file():
                continue

            spec = importlib.util.spec_from_file_location(py_path, candidate)
            if spec is None or spec.loader is None:
                continue

            mod = importlib.util.module_from_spec(spec)
            sys.modules[py_path] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception:
                sys.modules.pop(py_path, None)
                raise
            interpreter.modules_loaded[py_path] = mod
            return mod

    raise ImportError(f"No module named {py_path!r}")


def _load_mapple_module(
    file_path: pathlib.Path,
    interpreter: Interpreter,
    env: dict[str, Any],
):
    """Interpret a Mapple source file, returning its exports dict."""
    source = file_path.read_text()
    imported = Interpreter(source, file_path)

    imported.globals.define("exports", {})
    imported.modules_loaded = interpreter.modules_loaded

    for key, value in env.items():
        imported.globals.define(key, value)

    imported.globals.localsOnly = True
    imported.globals.define("__IS_MAIN__", False, True)

    setup(imported, imported.globals)
    imported.interpret()

    return dict(imported.globals.get("exports").value)


def _make_loader(interpreter: Interpreter):
    """Build the `load` function bound into the interpreter's globals."""

    def load(path: str, _env: dict[str, Any] | None = None):
        env = _env or {}
        ignore_cache = "ignore loaded module" in env

        # Explicit Python import: "py:pkg.module"
        if path.startswith("py:"):
            return _load_python_module(path[3:].replace("/", "."), interpreter)

        # Resolve the Mapple path.
        raw = pathlib.Path(
            path if path.endswith(FILE_EXTENSION) else path + FILE_EXTENSION
        )
        interp_dir = pathlib.Path(interpreter.file).resolve().parent
        candidates = _mapple_candidates(raw, interp_dir)
        file_path = next((p for p in candidates if p.is_file()), None)

        # Found a Mapple file → interpret it (with caching).
        if file_path is not None:
            if not ignore_cache and file_path in interpreter.modules_loaded:
                return interpreter.modules_loaded[file_path]

            result = _load_mapple_module(file_path, interpreter, env)
            if not ignore_cache:
                interpreter.modules_loaded[file_path] = result
            return result

        # Fall back to a Python import.
        py_path = (
            path[: -len(FILE_EXTENSION)] if path.endswith(FILE_EXTENSION) else path
        ).replace("/", ".")

        try:
            return _load_python_module(
                py_path,
                interpreter,
                search_dirs=[interp_dir, pathlib.Path.cwd(), LIBS_PATH],
            )
        except Exception as e:
            tried = "\n  ".join(str(x) for x in candidates)
            raise RuntimeError(
                f"Cannot find module: {path}\n"
                f"Tried Mapple:\n  {tried}\n"
                f"Tried Python import: {py_path}\n"
                f"Error: {e}",
            ) from e

    return load


# ─────────────────────────────────────────────────────────────────────────────
# Extension modules (driven by module_info.toml)
# ─────────────────────────────────────────────────────────────────────────────


def _import_extension_module(mod_file: str, modules_dir: pathlib.Path):
    """Import a module declared in module_info.toml, falling back to file-path load."""
    mod_name = mod_file[:-3] if mod_file.endswith(".py") else mod_file
    full_name = f"modules.{mod_name}"

    try:
        return importlib.import_module(full_name)
    except ImportError as e:
        candidate = modules_dir / mod_file
        if not candidate.is_file():
            raise
        spec = importlib.util.spec_from_file_location(full_name, candidate)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {mod_file}") from e
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)
        return mod


def _bind_extension_modules(globals_env: Environment) -> None:
    modules_dir = pathlib.Path(__file__).parent
    info_path = modules_dir / "module_info.toml"

    with open(info_path, "rb") as f:
        info = tomllib.load(f)

    for mod_file, bindings in info.items():
        mod = _import_extension_module(mod_file, modules_dir)
        for attr_name, bind_as in bindings.items():
            if not hasattr(mod, attr_name):
                raise AttributeError(f"{mod_file} has no attribute {attr_name!r}")
            globals_env.define(bind_as, getattr(mod, attr_name))


# ─────────────────────────────────────────────────────────────────────────────
# Builtins
# ─────────────────────────────────────────────────────────────────────────────


def _bind_builtin_helpers(globals_env: Environment) -> None:
    # Math helpers (builtins added on top of the math module namespace).
    mmath = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    mmath.update(abs=abs, max=max, min=min)

    globals_env.define("math", mmath)
    globals_env.define("json", json)
    globals_env.define("NaN", math.nan)
    globals_env.define("nil", None, True)
    globals_env.define("len", len)
    globals_env.define("hex", hex)
    globals_env.define("range", range)
    globals_env.define("iter", iter)

    def _slice(of_who, start, end=None):
        return of_who[start:end] if end is not None else of_who[start:]

    globals_env.define("slice", _slice)

    def shift(x: list):
        return x.pop(0)

    globals_env.define("shift", shift)

    def _next(it):
        try:
            return next(it)
        except StopIteration:
            return None

    _next.__name__ = "next"
    globals_env.define("next", _next)

    def _raise(x):
        raise x

    _raise.__name__ = "raise"
    globals_env.define("raise", _raise)


def _bind_types_and_exceptions(globals_env: Environment) -> None:
    for name, obj in vars(builtins).items():
        if isinstance(obj, type) and issubclass(obj, BaseException):
            globals_env.define(name, obj)

    globals_env.define("MappleError", MappleError)

    for name, obj in BUILTIN_VAR_TYPES.items():
        globals_env.define(name, obj)

    for t in (tuple, str, int, float, dict, list):
        globals_env.define(t.__name__, t)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────


def setup(interpreter: Interpreter, globals_env: Environment) -> None:
    """Populate the interpreter's globals with the extension-based standard
    library, the `load` function, and core builtins.

    Driven by `modules/module_info.toml`.
    """
    globals_env.define("load", _make_loader(interpreter))
    _bind_extension_modules(globals_env)
    _bind_builtin_helpers(globals_env)
    _bind_types_and_exceptions(globals_env)
