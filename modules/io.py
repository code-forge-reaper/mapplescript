"""
This module gives IO stuff to Mapple
"""
import builtins
from collections.abc import Iterable
from typing import Any


def _format(obj: Any) -> Any:
    # Custom string overload
    if isinstance(obj, dict) and "__Str" in obj:
        return obj["__Str"]()

    # MappleScript object instance
    if isinstance(obj, dict):
        if "__DefiningClass" in obj:
            cls = obj["__DefiningClass"]
            public = cls.get_public_instance_members(obj)
            return _format(public)

        # Regular dict (hide internal members)
        return {
            k: _format(v)
            for k, v in obj.items()
            if not (isinstance(k, str) and k.startswith("__"))
        }

    # Lists, tuples, sets, etc.
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
        return [_format(x) for x in obj]

    return obj


def pprint(*stuff: Any) -> None:
    print(*(_format(x) for x in stuff))


def write(t: Any, to: Any) -> None:
    print(_format(t), file=to)


binput = builtins.input  # noqa-ish, but pylint-clean
