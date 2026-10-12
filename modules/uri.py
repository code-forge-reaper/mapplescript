class Uri:
    @staticmethod
    def decode(s):
        return unquote(s)

    @staticmethod
    def encode(s):
        return quote(s)
