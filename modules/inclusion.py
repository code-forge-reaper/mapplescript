
# Has.<relation>(target, value) -> {target} Has {value} <relation>
class Has:
    @staticmethod
    def key(d, k):
        if not isinstance(d, dict):
            raise TypeError(f"Expected dict, got {type(d).__name__}")
        return k in d

    @staticmethod
    def value(d, v):
        return v in d.values()

    @staticmethod
    def inside(target, what):
        return what in target  # works for list, str, set, tuple

    @staticmethod
    def attr(target, what):
        return hasattr(target, what)
