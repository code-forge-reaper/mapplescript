from .controlFlow import ControlFlow

class BreakFlow(ControlFlow):
    def to_dict(self):
        return {"type": "BreakFlow"}
