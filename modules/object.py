from typing import Any

type ValidIndex = str | int


class Object:
    @staticmethod
    def keys(obj: dict[ValidIndex, Any]):  # pyright: ignore[reportExplicitAny]
        return list(obj.keys())

    @staticmethod  # most sane python typing:
    def get(  # pyright: ignore[reportAny]
        obj: dict[ValidIndex, Any],  # pyright: ignore[reportExplicitAny]
        key: ValidIndex,
        default: Any = None,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> Any:  # pyright: ignore[reportExplicitAny]
        return obj.get(key, default)  # pyright: ignore[reportAny]

    @staticmethod
    def values(obj):
        return list(obj.values())

    @staticmethod
    def delete(x, y):
        del x[y]

    @staticmethod
    def items(obj):
        return list(obj.items())

    @staticmethod
    def setattr(obj, key, value):
        setattr(obj, key, value)

    @staticmethod
    def getattr(obj, key):
        return getattr(obj, key)

    @staticmethod
    def hasattr(obj, key):
        return hasattr(obj, key)

    @staticmethod
    def delattr(obj, key):
        builtins.delattr(obj, key)

    @staticmethod
    def attrs(obj):
        return dir(obj)

    @staticmethod
    def type(obj):
        return type(obj)
