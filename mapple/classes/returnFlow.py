from .controlFlow import ControlFlow

class ReturnFlow(ControlFlow):
    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return {"type": "ReturnFlow", "value": self._serialize_value(self.value)}

    @staticmethod
    def _serialize_value(val):
        if hasattr(val, "to_dict"):
            return val.to_dict()
        return repr(val) if val is not None else None
