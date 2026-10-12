from collections.abc import Buffer
import pathlib
from typing import Literal

type PathLike = str | pathlib.Path


class Fs:
    @staticmethod
    def read(path: PathLike, mode: Literal["str", "byte"] = "str") -> str | bytes:
        p = pathlib.Path(path)
        return p.read_text() if mode == "str" else p.read_bytes()

    @staticmethod
    def open(path: PathLike):
        return pathlib.Path(path)

    @staticmethod
    def write(path: PathLike, contents: str | Buffer):
        p = pathlib.Path(path)
        if type(contents) == Buffer:
            return p.write_bytes(contents)
        else:
            return p.write_text(str(contents))

    @staticmethod
    def exists(path: PathLike):
        return pathlib.Path(path).exists()

    @staticmethod
    def isdir(path: PathLike):
        return pathlib.Path(path).is_dir()

    @staticmethod
    def listdir(path: PathLike = "."):
        return [p.name for p in pathlib.Path(path).iterdir()]

    @staticmethod
    def join(*parts: str | pathlib.Path):
        return str(pathlib.Path(*parts))
