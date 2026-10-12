import struct
import array


class Convert:
    @staticmethod
    def toInt(s):
        return int(s)

    @staticmethod
    def toTuple(s):
        return tuple(s)

    @staticmethod
    def toFloat(s):
        return float(s)

    @staticmethod
    def toNumber(s):
        if not isinstance(s, str):
            raise ValueError(f"this function expects a string, got {type(s)}")
        try:
            return int(s)
        except ValueError:
            return float(s)

    @staticmethod
    def toStr(thing):
        if isinstance(thing, list):
            return "".join(thing)

        return str(thing)

    @staticmethod
    def toBool(s):
        if isinstance(s, str):
            return s.lower() in ("true", "1", "yes")
        return bool(s)

    @staticmethod
    def toArray(s, n=None):
        if n:
            return array.array(s, n)
        return list(s)

    @staticmethod
    def toDict(s):
        return dict(s)

    @staticmethod
    def toChar(i):
        return chr(i)

    @staticmethod
    def toCharCode(s):
        return ord(s)

    @staticmethod
    def toBytes(data, encoding: str | None = None):
        if isinstance(data, str):
            if not isinstance(encoding, str):
                raise ValueError("expected encoding to be string")
            return bytes(data, encoding)
        return bytes(data)

    @staticmethod
    def toByteArray(s, enc="utf8"):
        # Already bytes/bytearray → pass through
        if isinstance(s, (bytes, bytearray)):
            return bytearray(s)

        # int → single byte
        if isinstance(s, int):
            return bytearray([s & 0xFF])

        # float → 8-byte little-endian double
        if isinstance(s, float):
            return bytearray(struct.pack("<d", s))

        # iterable of ints → convert each to byte
        if isinstance(s, (list, tuple)):
            return bytearray([x & 0xFF for x in s])

        # string → encode
        if isinstance(s, str):
            return bytearray(s, enc)

        raise TypeError(f"Convert.toBytes: unsupported type {type(s)}")
