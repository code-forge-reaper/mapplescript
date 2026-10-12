import importlib
import importlib.util
import pathlib

import sys
from typing import Any

from mapple.conf import LIBS_PATH, FILE_EXTENSION
from mapple.novaenv import Environment
from mapple.runtime import Interpreter


def setup(interpreter: Interpreter, globals_env: Environment):
    def load(
        path: str,
        _env: dict[str, Any] | None = None,  # pyright: ignore[reportExplicitAny]
    ):  # const <modname> = load("modname")
        env = _env or {}
        ignore_cache = "ignore loaded module" in env

        # ── FORCE Python import ──
        if path.startswith("py:"):
            return _load_python(path[3:].replace("/", "."))

        # ── Try Nova first ──
        # Keep `raw` *relative* here; resolve only after joining to a root.
        raw = pathlib.Path(
            path if path.endswith(FILE_EXTENSION) else path + FILE_EXTENSION
        )
        interp_dir = pathlib.Path(interpreter.file).resolve().parent

        candidates = [
            raw,  # as-given (resolved against CWD)
            interp_dir / raw,  # sibling of the currently-executing file
            pathlib.Path.cwd() / raw,
            LIBS_PATH / raw,
        ]

        # Resolve + dedupe, preserving order
        possible_locations = []
        seen = set()
        for c in candidates:
            r = c.resolve()
            if r not in seen:
                seen.add(r)
                possible_locations.append(r)

        file_path = next((p for p in possible_locations if p.is_file()), None)

        # ── If Nova module found → load it ──
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

        py_path = (path[:-5] if path.endswith(FILE_EXTENSION) else path).replace(
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
                f"Tried Nova:\n  {tried}\n"
                f"Tried Python import: {py_path}\n"
                f"Error: {e}",
            )

    def _load_python(py_path: str, search_dirs=()):
        if py_path in interpreter.modules_loaded:
            return interpreter.modules_loaded[py_path]

        # Fast path: normal import (installed packages, anything already on sys.path)
        try:
            result = importlib.import_module(py_path)
            interpreter.modules_loaded[py_path] = result
            return result
        except ImportError:
            pass

        # Fallback: find a matching .py alongside the loading Nova module
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
