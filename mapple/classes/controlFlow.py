# --- Control Flow Classes ---
class ControlFlow:
    """Base class for control flow signals"""

    def to_dict(self):
        return {"type": self.__class__.__name__}

