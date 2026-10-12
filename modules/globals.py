""" from typing import Any

from mapple.nodes import NovaError
from mapple.typechecker import BUILTIN_VAR_TYPES
from mapple.novaenv import Environment
from mapple.runtime import Interpreter
from mapple.conf import LIBS_PATH
import importlib
import importlib.util
import pathlib
import sys

impLib = importlib.import_module

import math
import re
import array
import datetime, os
import time, json
from urllib.parse import unquote, quote
import struct, builtins



# --- Global Initialization ---
def init_globals(interpreter, globals_env):

    def _slice(ofWho, start, end=None):
        if end is not None:
            return ofWho[start:end]
        else:
            return ofWho[start:]

    def shift(x: list[Any]):
        v = x.pop(0)
        return v

    # args = sys.argv[2:] # Skip script name and NovaScript file name

    mmath = {}
    for k, v in math.__dict__.items():
        if not k.startswith("_"):
            mmath[k] = v
    mmath["abs"] = abs
    mmath["max"] = max
    mmath["min"] = min


    builtin_values: dict[str, object] = {
        name: obj
        for name, obj in vars(builtins).items()
        if isinstance(obj, type) and issubclass(obj, BaseException)
    }
    builtin_values["NovaError"] = NovaError
    builtin_values.update(BUILTIN_VAR_TYPES)

    for e, v in builtin_values.items():
        globals_env.define(
            e, v
        )  # more for error checking and better controll over what to raise instead of Runtime.panic
    # name | value | const?
    globals_env.define("print", pprint)
    globals_env.define("write", lambda t, to: print(t, file=to))
    globals_env.define("input", input)
    globals_env.define("shift", shift)
    globals_env.define("Logger", Logger)
    globals_env.define("Is", Is)
    globals_env.define("Has", Has)
    globals_env.define("Convert", Convert)
    globals_env.define("len", len)
    globals_env.define("hex", hex)
    globals_env.define("json", json)
    globals_env.define("load", load)
    globals_env.define("range", range)
    globals_env.define("slice", _slice)
    globals_env.define("math", mmath)
    globals_env.define("NaN", math.nan)
    globals_env.define("nil", None, True)
    globals_env.define("Runtime", Runtime)
    globals_env.define("Uri", Uri)
    globals_env.define("iter", iter)

    def nx(it):
        try:
            return next(it)
        except StopIteration:
            return None

    nx.__name__ = "next"
    globals_env.define("next", nx)
    globals_env.define("Fs", Fs)
    globals_env.define("Object", Object)
    globals_env.define("Time", Time)

    def r(x):
        raise x

    r.__name__ = "raise"
    globals_env.define("raise", r)
    types = [
        tuple, str, int, float, dict, list
    ]
    for t in types:
        globals_env.define(t.__name__, t)
 """