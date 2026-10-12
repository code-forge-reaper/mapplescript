from urllib.parse import unquote, quote


class Uri:
    @staticmethod
    def decode(s: str) -> str:
        return unquote(s)

    @staticmethod
    def encode(s: str) -> str:
        return quote(s)
