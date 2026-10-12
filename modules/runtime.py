from typing import NoReturn


import os
import sys


class MapplePanic(Exception):
    """Raised when Mapple explicitly panics."""


class Runtime:
    @staticmethod
    def exit(code: int = 0):
        sys.exit(code)

    args: list[str] = sys.argv[1:]

    @staticmethod
    def env(key: str | None = None):
        if key:
            return os.environ.get(key)
        return dict(os.environ)  # Return a copy of the environment variables

    @staticmethod
    def panic(reason: str, *rest: object) -> NoReturn:
        if rest:
            reason = reason.format(*rest)
        raise MapplePanic(reason)
