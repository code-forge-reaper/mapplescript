class Is:
    @staticmethod
    def string(s):
        return isinstance(s, str)

    @staticmethod
    def number(n):
        return isinstance(n, (int, float))

    @staticmethod
    def instance(what, parent):
        return isinstance(what, parent)

    @staticmethod
    def int(n):
        return isinstance(n, (int))

    @staticmethod
    def float(n):
        return isinstance(n, (float))

    @staticmethod
    def boolean(b):
        return isinstance(b, bool)

    @staticmethod
    def list(a):
        return isinstance(a, list)

    @staticmethod
    def dict(a):
        return isinstance(a, dict)

    @staticmethod
    def callable(c):
        return callable(c)
