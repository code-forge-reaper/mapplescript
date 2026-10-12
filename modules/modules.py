import importlib
import importlib.util
import pathlib
import sys
import tomllib
from typing import Any

from mapple.conf import LIBS_PATH, FILE_EXTENSION, ROOT
from mapple.mappleenv import Environment
from mapple.runtime import Interpreter


def setup(interpreter: Interpreter, globals_env: Environment):
    """Populate the interpreter globals with the extension-based standard library
    and the `load` function. Controlled by modules/module_info.toml.
    """

    def load(
        path: str,
        _env: dict[str, Any] | None = None,
    ):
        env = _env or {}
        ignore_cache = "ignore loaded module" in env

        # ── FORCE Python import ──
        if path.startswith("py:"):
            return _load_python(path[3:].replace("/", "."))

        # ── Try Mapple first ──
        raw = pathlib.Path(
            path if path.endswith(FILE_EXTENSION) else path + FILE_EXTENSION
        )
        interp_dir = pathlib.Path(interpreter.file).resolve().parent

        candidates = [
            raw,
            interp_dir / raw,
            pathlib.Path.cwd() / raw,
            LIBS_PATH / raw,
        ]

        possible_locations = []
        seen = set()
        for c in candidates:
            r = c.resolve()
            if r not in seen:
                seen.add(r)
                possible_locations.append(r)

        file_path = next((p for p in possible_locations if p.is_file()), None)

        if file_path is not None:
            if not ignore_cache and file_path in interpreter.modules_loaded:
                return interpreter.modules_loaded[file_path]

            with open(file_path) as f:
                source = f.read()

            imported = Interpreter(source, file_path)
            imported.globals.define("exports", {})
            imported.modules_loaded = interpreter.modules_loaded
            for k, v in env.items():
                imported.globals.define(k, v)
            imported.globals.localsOnly = True

            imported.globals.define("__IS_MAIN__", False, True)
            setup(imported, imported.globals)
            imported.interpret()

            result = dict(imported.globals.get("exports").value)
            if not ignore_cache:
                interpreter.modules_loaded[file_path] = result
            return result

        py_path = (path[: -len(FILE_EXTENSION)] if path.endswith(FILE_EXTENSION) else path).replace(
            "/", "."
        )
        try:
            return _load_python(
                py_path,
                search_dirs=[interp_dir, pathlib.Path.cwd(), LIBS_PATH],
            )
        except Exception as e:
            tried = "\n  ".join(str(x) for x in possible_locations)
            raise RuntimeError(
                f"Cannot find module: {path}\n"
                f"Tried Mapple:\n  {tried}\n"
                f"Tried Python import: {py_path}\n"
                f"Error: {e}",
            )

    def _load_python(py_path: str, search_dirs=()):
        if py_path in interpreter.modules_loaded:
            return interpreter.modules_loaded[py_path]

        try:
            result = importlib.import_module(py_path)
            interpreter.modules_loaded[py_path] = result
            return result
        except ImportError:
            pass

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

    # Bind the load function itself
    globals_env.define("load", load)

    # Load and bind everything declared in module_info.toml
    info_path = pathlib.Path(__file__).parent / "module_info.toml"
    with open(info_path, "rb") as f:
        info = tomllib.load(f)

    modules_dir = pathlib.Path(__file__).parent
    for mod_file, bindings in info.items():
        # mod_file e.g. "filesystem.py"
        mod_name = mod_file[:-3] if mod_file.endswith(".py") else mod_file
        full_name = f"modules.{mod_name}"
        try:
            mod = importlib.import_module(full_name)
        except ImportError:
            # Fallback: load by file path
            candidate = modules_dir / mod_file
            if not candidate.is_file():
                raise
            spec = importlib.util.spec_from_file_location(full_name, candidate)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load {mod_file}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[full_name] = mod
            spec.loader.exec_module(mod)

        for attr_name, bind_as in bindings.items():
            if not hasattr(mod, attr_name):
                raise AttributeError(f"{mod_file} has no attribute {attr_name!r}")
            globals_env.define(bind_as, getattr(mod, attr_name))

    # Core builtins that are not in the extension modules
    import math
    import json
    import builtins

    mmath = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    mmath["abs"] = abs
    mmath["max"] = max
    mmath["min"] = min

    globals_env.define("math", mmath)
    globals_env.define("json", json)
    globals_env.define("NaN", math.nan)
    globals_env.define("nil", None, True)
    globals_env.define("input", input)
    globals_env.define("len", len)
    globals_env.define("hex", hex)
    globals_env.define("range", range)
    globals_env.define("iter", iter)

    def _slice(ofWho, start, end=None):
        if end is not None:
            return ofWho[start:end]
        return ofWho[start:]

    globals_env.define("slice", _slice)

    def shift(x: list):
        return x.pop(0)

    globals_env.define("shift", shift)

    def nx(it):
        try:
            return next(it)
        except StopIteration:
            return None

    nx.__name__ = "next"
    globals_env.define("next", nx)

    def r(x):
        raise x

    r.__name__ = "raise"
    globals_env.define("raise", r)

    # Expose common exception types + MappleError
    from mapple.nodes import MappleError
    from mapple.typechecker import BUILTIN_VAR_TYPES

    for name, obj in vars(builtins).items():
        if isinstance(obj, type) and issubclass(obj, BaseException):
            globals_env.define(name, obj)
    globals_env.define("MappleError", MappleError)
    for name, obj in BUILTIN_VAR_TYPES.items():
        globals_env.define(name, obj)

    for t in (tuple, str, int, float, dict, list):
        globals_env.define(t.__name__, t)
